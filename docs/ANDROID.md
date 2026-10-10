# Android APK

`android/` contains a thin Java WebView client with no native binaries, minSdk 23 (Android 6+), compileSdk/targetSdk 36. It does not scrape on the phone. Deploy the API and worker to an HTTPS server first. Android 9 falls within the declared API range, but no physical-device compatibility or performance test was performed.

## Build through GitHub, no coding on your phone

1. Deploy PricePulse to your own HTTPS origin, for example `https://prices.yourdomain.in`.
2. Open this repository's **Actions** tab → **Build Android debug APK** → **Run workflow**.
3. Enter your actual HTTPS origin in `app_url`. Do not enter a GitHub repository URL.
4. After the workflow succeeds, download the `pricepulse-debug-apk` artifact, extract it, and install `app-debug.apk` on your phone.

This workflow is manual; no APK has been built by the initial delivery because there is no hosted application URL yet. The workflow downloads Android SDK and Gradle dependencies from their official registries and needs network access.

## Android Studio

Open `android/` in Android Studio. Install Android SDK platform 36 and Build Tools 36.0.0, use JDK 17 and Gradle 8.13 with Android Gradle Plugin 8.11.1. This toolchain follows the [AGP 8.11 compatibility table](https://developer.android.com/build/releases/agp-8-11-0-release-notes).

Set `APP_URL=https://your-origin` in your local `android/gradle.properties`, or pass `-PAPP_URL=https://your-origin`. The placeholder intentionally refuses to run. APP_URL must be an HTTPS origin with no credentials, query or subpath. Use the IDE's build menu to build APKs. For terminal builds with Gradle installed:

```sh
gradle -p android -PAPP_URL=https://your-origin assembleDebug
```

For a Play Store release, create and securely retain your own signing key, use Android Studio's **Generate Signed Bundle / APK**, and choose an AAB. Check the current Play target/API and publishing requirements before submission. Keystores and passwords must never be committed.

## Device behavior

- Update Chrome / Android System WebView before testing on older phones.
- The app loads the lightweight web interface and leaves all collection work on the server.
- HTTPS external store navigation opens the default browser. File/content URLs and mixed HTTP content are blocked. No JavaScript native bridge is exposed.
- Closing the app does not stop the server's monitoring worker. Notifications remain recorded on the server and appear when the app opens again.
- Browser `Notification` support is not guaranteed in Android WebView. This client does **not** implement native background push. Add a native FCM client, token registration and notification delivery before advertising closed-app notifications.
- Clearing app data removes the anonymous watchlist cookie. Cross-device account sync is not implemented.
