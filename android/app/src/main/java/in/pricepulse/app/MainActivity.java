package in.pricepulse.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.widget.Toast;

/** Thin online Android client. Collection and scheduling run on the server. */
public class MainActivity extends Activity {
    private WebView web;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (BuildConfig.APP_URL.contains("example.invalid")) {
            Toast.makeText(this,"Build with your deployed HTTPS APP_URL first",Toast.LENGTH_LONG).show(); finish(); return;
        }
        web = new WebView(this);
        setContentView(web);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri target = request.getUrl(); Uri own = Uri.parse(BuildConfig.APP_URL);
                if ("https".equals(target.getScheme()) && own.getHost().equals(target.getHost()) && own.getPort()==target.getPort()) return false;
                if ("https".equals(target.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW,target)); }
                    catch (android.content.ActivityNotFoundException e) { Toast.makeText(MainActivity.this,"No browser available",Toast.LENGTH_SHORT).show(); }
                }
                return true;
            }
        });
        if (state==null || web.restoreState(state)==null) web.loadUrl(BuildConfig.APP_URL);
    }
    @Override public void onBackPressed() { if(web!=null && web.canGoBack()) web.goBack(); else super.onBackPressed(); }
    @Override protected void onSaveInstanceState(Bundle state) { super.onSaveInstanceState(state); if(web!=null) web.saveState(state); }
    @Override protected void onDestroy() { if(web!=null) {web.stopLoading();web.destroy();} super.onDestroy(); }
}
