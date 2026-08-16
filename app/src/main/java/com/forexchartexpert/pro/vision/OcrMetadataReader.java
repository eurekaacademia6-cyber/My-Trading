package com.forexchartexpert.pro.vision;

import android.graphics.Bitmap;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class OcrMetadataReader implements AutoCloseable {
    public interface Callback { void onMetadata(String symbol, String timeframe, String raw); }
    private final TextRecognizer recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
    private static final Pattern PAIR=Pattern.compile("\\b([A-Z]{3})[\\s/_-]?([A-Z]{3})\\b");
    private static final Pattern TF=Pattern.compile("\\b(M1|M3|M5|M15|M30|H1|H2|H4|D1|W1|MN1)\\b",Pattern.CASE_INSENSITIVE);
    public void read(Bitmap bitmap, Callback cb){
        if(bitmap==null)return;
        recognizer.process(InputImage.fromBitmap(bitmap,0)).addOnSuccessListener(t->{
            String raw=t.getText().toUpperCase(Locale.US); String sym="AUTO",tf="AUTO";
            Matcher m=PAIR.matcher(raw); if(m.find()) sym=m.group(1)+m.group(2);
            Matcher f=TF.matcher(raw); if(f.find()) tf=f.group(1).toUpperCase(Locale.US);
            cb.onMetadata(sym,tf,raw);
        }).addOnFailureListener(e->cb.onMetadata("AUTO","AUTO",""));
    }
    @Override public void close(){recognizer.close();}
}
