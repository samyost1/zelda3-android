"""Exercise the production atomic publisher on legacy and modern API paths."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'app/src/main/java/com/dishii/zelda3'


class AssetPublishTests(unittest.TestCase):
    def test_legacy_api_and_failed_replacement_preserve_old_assets(self):
        jdk=Path('C:/Program Files/Java/jdk-17/bin')
        javac=str(jdk/'javac.exe') if (jdk/'javac.exe').exists() else shutil.which('javac')
        java=str(jdk/'java.exe') if (jdk/'java.exe').exists() else shutil.which('java')
        if not javac or not java:self.skipTest('Requires a JDK')
        self.assertTrue((JAVA/'AssetFileWriter.java').exists(), 'API-compatible atomic asset publisher exists')
        sources={
          'android/os/Build.java': 'package android.os; public class Build { public static class VERSION { public static int SDK_INT; } }',
          'android/system/ErrnoException.java': 'package android.system; public class ErrnoException extends Exception {}',
          'android/system/Os.java': '''package android.system; import java.nio.file.*;
            public class Os { public static boolean fail; public static int calls;
              public static void rename(String a,String b) throws ErrnoException {
                calls++; if(fail)throw new ErrnoException();
                try {Files.move(Paths.get(a),Paths.get(b),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
                catch(Exception e){throw new ErrnoException();}
              }
            }''',
          'com/dishii/zelda3/PublishTest.java': '''package com.dishii.zelda3;
            import java.nio.file.*;import java.io.*;import java.util.*;
            public class PublishTest {
              static void check(boolean b){if(!b)throw new AssertionError();}
              public static void main(String[] args)throws Exception {
                Path dir=Paths.get(args[0]),temp=dir.resolve("assets.tmp"),out=dir.resolve("assets.dat");
                android.os.Build.VERSION.SDK_INT=16;
                Files.write(temp,new byte[]{1,2});AssetFileWriter.replace(temp.toFile(),out.toFile());
                check(Arrays.equals(Files.readAllBytes(out),new byte[]{1,2}));
                if(args.length>1)return; // modern classes are absent in this run
                check(android.system.Os.calls==0);
                android.os.Build.VERSION.SDK_INT=21;
                Files.write(temp,new byte[]{3,4});android.system.Os.fail=true;
                try {AssetFileWriter.replace(temp.toFile(),out.toFile());throw new AssertionError();}
                catch(IOException expected){}
                check(Arrays.equals(Files.readAllBytes(out),new byte[]{1,2}) && Files.exists(temp));
                android.system.Os.fail=false;AssetFileWriter.replace(temp.toFile(),out.toFile());
                check(Arrays.equals(Files.readAllBytes(out),new byte[]{3,4}) && !Files.exists(temp));
              }
            }'''
        }
        with tempfile.TemporaryDirectory(prefix='zelda-asset-publish-') as temp:
            d=Path(temp); files=[]
            for name,text in sources.items():
                p=d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(str(p))
            subprocess.run([javac,'--release','8','-Xlint:-options','-d',str(d),str(JAVA/'AssetFileWriter.java')]+files,check=True)
            run_dir=d/'normal';run_dir.mkdir()
            subprocess.run([java,'-cp',str(d),'com.dishii.zelda3.PublishTest',str(run_dir)],check=True)
            # Legacy first import must not even resolve unavailable API21 classes.
            system=(d/'android/system').resolve()
            assert system.is_relative_to(d.resolve())
            shutil.rmtree(system)
            legacy=d/'legacy';legacy.mkdir()
            subprocess.run([java,'-cp',str(d),'com.dishii.zelda3.PublishTest',str(legacy),'legacy'],check=True)
