package com.forexchartexpert.pro.analysis;

import android.content.Context;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public final class SignalAuditLog {
    private final File file;
    public SignalAuditLog(Context c){file=new File(c.getFilesDir(),"signal_audit.csv");}
    public synchronized void append(String line){
        try(FileWriter w=new FileWriter(file,true)){w.write(line.replace("\n"," ")+"\n");}catch(IOException ignored){}
    }
}
