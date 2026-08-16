name: Build Android APK

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build-apk:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up JDK 17
        uses: actions/setup-java@v5
        with:
          distribution: temurin
          java-version: '17'

      - name: Set up Android SDK
        uses: android-actions/setup-android@v3

      - name: Install Android SDK components
        run: |
          yes | sdkmanager --licenses || true
          sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"

      - name: Set up Gradle 8.13
        uses: gradle/actions/setup-gradle@v6
        with:
          gradle-version: '8.13'

      - name: Show build environment
        run: |
          java -version
          gradle --version

      - name: Build debug APK
        run: gradle assembleDebug --stacktrace

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: ForexChartExpert-debug-apk
          path: app/build/outputs/apk/debug/*.apk
          if-no-files-found: error
