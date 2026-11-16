package sa.urtv.home;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.webkit.WebResourceResponse;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Collections;
import java.util.Date;
import java.util.Locale;

import javax.net.ssl.HttpsURLConnection;

/** The home WebView receives only booking titles, room names, and times. Authentication and the calendar response stay in native code. */
final class HallBookings {
    static final String FEED = "https://hall-bookings.urtv.invalid/today.json";
    private static final String CALENDAR = "https://hallsbooking.mtc.edu.om/api/calendar/";
    private static final Uri TOKEN = Uri.parse("content://sa.urtv.screensaver.config/hall-bookings-token");

    private HallBookings() {}

    static WebResourceResponse fetch(Context context) {
        try {
            String token = token(context);
            if (token.isEmpty()) return response("{\"state\":\"unconfigured\"}");
            SimpleDateFormat date = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            date.setTimeZone(ZoneFix.zone("Asia/Muscat"));
            String day = date.format(new Date());
            HttpsURLConnection connection = (HttpsURLConnection) new URL(CALENDAR + "?start=" + day + "&end=" + day).openConnection();
            try {
                connection.setInstanceFollowRedirects(false);
                connection.setUseCaches(false);
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(10000);
                connection.setRequestProperty("Accept", "application/json");
                connection.setRequestProperty("Authorization", "Token " + token);
                int status = connection.getResponseCode();
                if (status == 401 || status == 403) return response("{\"state\":\"denied\"}");
                if (status != 200) return response("{\"state\":\"offline\"}");
                try (InputStream in = connection.getInputStream()) {
                    return response(schedule(day, new String(Bounded.readAll(in, Bounded.JSON_MAX), StandardCharsets.UTF_8)));
                }
            } finally {
                connection.disconnect();
            }
        } catch (IOException | JSONException | RuntimeException error) {
            return response("{\"state\":\"offline\"}");
        }
    }

    private static String token(Context context) {
        if (!HomePage.providerIsOurs(context)) return "";
        try (Cursor cursor = context.getContentResolver().query(TOKEN, null, null, null, null)) {
            if (cursor == null || !cursor.moveToFirst() || cursor.isNull(0)) return "";
            String value = cursor.getString(0);
            return value.matches("[a-fA-F0-9]{40}") ? value : "";
        }
    }

    static String schedule(String day, String body) throws JSONException {
        JSONArray results = new JSONObject(body).getJSONArray("results");
        JSONArray rows = new JSONArray();
        for (int i = 0; i < results.length(); i++) {
            JSONObject booking = results.getJSONObject(i);
            String ar = booking.isNull("hall_name_ar") ? "" : booking.getString("hall_name_ar").trim();
            String en = booking.isNull("hall_name_en") ? "" : booking.getString("hall_name_en").trim();
            if (ar.isEmpty() && en.isEmpty()) continue;
            rows.put(new JSONObject().put("ar", ar).put("en", en)
                .put("title", booking.isNull("title") ? "" : booking.optString("title", "").trim())
                .put("start", time(booking.optString("from_time", "")))
                .put("end", time(booking.optString("to_time", ""))));
        }
        return new JSONObject().put("state", "ok").put("date", day).put("rows", rows).toString();
    }

    private static String time(String value) {
        return value.matches("(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9](?:\\.[0-9]+)?)?") ? value.substring(0, 5) : "";
    }

    private static WebResourceResponse response(String json) {
        return new WebResourceResponse("application/json", "UTF-8", 200, "OK",
            Collections.singletonMap("Cache-Control", "no-store"),
            new ByteArrayInputStream(json.getBytes(StandardCharsets.UTF_8)));
    }
}
