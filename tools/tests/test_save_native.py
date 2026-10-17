"""Exercise production checked-save and thumbnail code with injectable file failures."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from test_gamepad_native import SRC, toolchain


def function(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    i = opening + 1
    while depth:
        if source[i] == '{': depth += 1
        if source[i] == '}': depth -= 1
        i += 1
    return source[start:i] + '\n'


class NativeSaveTests(unittest.TestCase):
    def test_file_failures_and_thumbnail_identity(self):
        tc = toolchain()
        if os.name != 'nt' or not tc or not (tc / 'clang.exe').exists():
            self.skipTest('Requires Windows and Android NDK')
        rtl = (SRC / 'zelda_rtl.c').read_text()
        screen = (SRC / 'second_screen.c').read_text()
        source = r'''
typedef unsigned char uint8;
typedef unsigned int uint32;
typedef unsigned long long uint64, size_t;
typedef _Bool bool;
#define true 1
#define false 0
#define NULL ((void*)0)
#define ENOENT 2
#define SEEK_END 2
#define SEEK_SET 0
#define kSaveLoad_Save 0
#define kSsThumbW 128
#define kSsThumbH 112
static int errno;
typedef int FILE;
typedef int SDL_RWops;
typedef struct { uint8 *data; size_t size; } ByteArray;
static int exists = 1, denied, write_ok = 1, close_ok = 1, rename_ok = 1, read_ok = 1;
static int loaded, saved, png_writes;
static uint8 filedata[128], allocated[128];
static long filesize = 36;
static int state_recorder, handle;
void *memcpy(void *d, const void *s, size_t n) { for (size_t i=0;i<n;i++) ((uint8*)d)[i]=((const uint8*)s)[i]; return d; }
void *malloc(size_t n) { return allocated; }
void free(void *p) {}
FILE *fopen(const char *p, const char *m) { if (denied) { errno=13; return NULL; } if (!exists) { errno=ENOENT; return NULL; } return &handle; }
int fseek(FILE *f, long off, int origin) { return 0; }
long ftell(FILE *f) { return filesize; }
size_t fread(void *p, size_t s, size_t n, FILE *f) { if (!read_ok) return 0; memcpy(p,filedata,n); return n; }
int fclose(FILE *f) { return 0; }
bool GetStatePath(int slot, const char *suffix, char *out, size_t size) { out[0]=suffix[0]; out[1]=0; return true; }
SDL_RWops *SDL_RWFromFile(const char *p, const char *mode) { return denied ? NULL : &handle; }
bool StateRecorder_Save(int *sr, SDL_RWops *f) { return write_ok; }
int SDL_RWclose(SDL_RWops *f) { return close_ok ? 0 : -1; }
int rename(const char *a, const char *b) { if (rename_ok) saved++; return rename_ok ? 0 : -1; }
int remove(const char *p) { return 0; }
void saveFunc(void) {}
void SaveSnesState(void (*f)(void), ByteArray *a) { a->size=4; }
void ByteArray_Destroy(ByteArray *a) {}
SDL_RWops *SDL_RWFromConstMem(void *p, int size) { return &handle; }
void StateRecorder_Load(int *sr, SDL_RWops *f, bool replay) { loaded++; }
size_t SDL_RWwrite(SDL_RWops *f, const void *data, size_t size, size_t n) { png_writes++; return write_ok ? n : 0; }
void SDL_AtomicLock(int *lock) {}
void SDL_AtomicUnlock(int *lock) {}
static int g_state_lock, g_state_generation[6], g_thumb_slot, g_thumb_generation;
static int g_ss_thumb_state, g_state_result, g_state_head, g_state_count, g_state_queue[16];
static uint32 g_ss_thumb[128*112], output[128*112];
'''
        source += function(rtl, 'int SaveLoadSlotChecked(')
        for signature in ['static void QueueState(', 'int SS_PollStateResult(',
                          'bool SS_TakeStateThumbnail(', 'bool SS_CommitThumbnail(']:
            source += function(screen, signature)
        source += r'''
#define CHECK(x) if (!(x)) return __LINE__;
int tests(void) {
  uint32 *hdr = (uint32 *)filedata;
  hdr[0]=1; hdr[6]=4;
  CHECK(SaveLoadSlotChecked(1, 1)==2 && loaded==1);
  exists=0; CHECK(SaveLoadSlotChecked(1, 1)==3); exists=1;
  filesize=0; CHECK(SaveLoadSlotChecked(1, 1)==3);
  filesize=35; CHECK(SaveLoadSlotChecked(1, 1)==4);
  filesize=36; hdr[0]=2; CHECK(SaveLoadSlotChecked(1, 1)==4); hdr[0]=1;
  hdr[6]=8; CHECK(SaveLoadSlotChecked(1, 1)==4); hdr[6]=4;
  read_ok=0; CHECK(SaveLoadSlotChecked(1, 1)==4); read_ok=1;
  denied=1; CHECK(SaveLoadSlotChecked(1, 1)==4); CHECK(SaveLoadSlotChecked(0,1)==4); denied=0;
  CHECK(loaded==1);
  CHECK(SaveLoadSlotChecked(0,1)==1 && saved==1);
  write_ok=0; CHECK(SaveLoadSlotChecked(0,1)==4 && saved==1); write_ok=1;
  close_ok=0; CHECK(SaveLoadSlotChecked(0,1)==4 && saved==1); close_ok=1;
  rename_ok=0; CHECK(SaveLoadSlotChecked(0,1)==4 && saved==1); rename_ok=1;
  CHECK(SaveLoadSlotChecked(0,-1)==4 && SaveLoadSlotChecked(0,6)==4);
  QueueState(1,true); QueueState(3,false);
  CHECK(g_state_count==2 && g_state_queue[0]==2 && g_state_queue[1]==7);
  g_state_count=0;
  for (int i=0;i<16;i++) QueueState(1,true);
  QueueState(2,true); CHECK(g_state_count==16 && SS_PollStateResult()==((2<<8)|4));
  CHECK(SS_PollStateResult()==0);
  int meta[2];
  g_thumb_slot=3; g_thumb_generation=7; g_state_generation[3]=7; g_ss_thumb_state=2;
  g_ss_thumb[0]=123;
  CHECK(SS_TakeStateThumbnail(output,meta) && meta[0]==3 && meta[1]==7 && output[0]==123);
  CHECK(!SS_TakeStateThumbnail(output,meta));
  g_state_generation[3]=8;
  CHECK(!SS_CommitThumbnail(3,7,filedata,8) && png_writes==0);
  CHECK(SS_CommitThumbnail(3,8,filedata,8) && png_writes==1);
  write_ok=0;
  CHECK(!SS_CommitThumbnail(3,8,filedata,8));
  write_ok=1;
  CHECK(SaveLoadSlotChecked(0,0)==1);
  int before_saved=saved, before_loaded=loaded;
  CHECK(SaveLoadSlotChecked(1,0)==2 && loaded==before_loaded+1);
  exists=0; CHECK(SaveLoadSlotChecked(1,0)==3); exists=1;
  filesize=0; CHECK(SaveLoadSlotChecked(1,0)==3); filesize=36;
  hdr[0]=2; CHECK(SaveLoadSlotChecked(1,0)==4); hdr[0]=1;
  write_ok=0; CHECK(SaveLoadSlotChecked(0,0)==4 && saved==before_saved); write_ok=1;
  close_ok=0; CHECK(SaveLoadSlotChecked(0,0)==4 && saved==before_saved); close_ok=1;
  rename_ok=0; CHECK(SaveLoadSlotChecked(0,0)==4 && saved==before_saved); rename_ok=1;
  CHECK(loaded==before_loaded+1);
  g_state_count=0; QueueState(0,true);
  CHECK(g_state_count==0); // manual UI still cannot address autosave

  return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix='zelda3-save-tests-') as directory:
            folder = Path(directory)
            (folder / 'test.c').write_text(source)
            subprocess.run([str(tc / 'clang.exe'), '--target=x86_64-pc-windows-msvc', '-O1',
                            '-ffreestanding', '-fno-stack-protector', '-c', str(folder / 'test.c'),
                            '-o', str(folder / 'test.obj')], check=True)
            subprocess.run([str(tc / 'ld.lld.exe'), '-flavor', 'link', '/entry:tests', '/subsystem:console',
                            '/nodefaultlib', '/out:' + str(folder / 'test.exe'), str(folder / 'test.obj')], check=True)
            result = subprocess.run([str(folder / 'test.exe')])
            self.assertEqual(result.returncode, 0, f'Native assertion at generated C line {result.returncode}')


if __name__ == '__main__':
    unittest.main()
