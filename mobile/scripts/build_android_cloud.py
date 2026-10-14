"""Debug build using the cloud's retained toolchain and supported proxy/CA trust."""
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

project = Path(__file__).resolve().parents[1]
environ = dict(os.environ)
for name, path in [('JAVA_HOME','/workspace/jdk17'), ('ANDROID_HOME','/workspace/android-sdk'), ('ANDROID_USER_HOME','/workspace/.android-user'), ('GRADLE_USER_HOME','/workspace/.gradle-pulse')]:
    if name not in environ:
        environ[name] = path
if not (project/'android/gradlew').is_file():
    raise SystemExit('Generate Android with Expo prebuild first; see docs/MOBILE_RELEASE.md.')
environ.update(EXPO_NO_TELEMETRY='1', EXPO_OFFLINE='1', NODE_ENV='development')
options = []
trust = Path('/etc/ssl/certs/java/cacerts')
if trust.is_file():
    options.append('-Djavax.net.ssl.trustStore='+str(trust))
proxy=urlsplit(environ.get('HTTPS_PROXY',''))
if proxy.hostname:
    for scheme in ['http','https']:
        options.extend([f'-D{scheme}.proxyHost={proxy.hostname}',f'-D{scheme}.proxyPort={proxy.port or 80}'])
environ['JAVA_OPTS']=environ.get('JAVA_OPTS','')+' '+' '.join(options)
raise SystemExit(subprocess.call(['./gradlew','--no-daemon','--max-workers=2',':app:assembleDebug','-PreactNativeArchitectures=arm64-v8a'],cwd=project/'android',env=environ))
