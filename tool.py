#!/usr/bin/env python3
"""Audit ZIP members without extracting them."""
import argparse,json,pathlib,sys,unittest,zipfile
from pathlib import PurePosixPath
def audit(path,max_ratio=1000,max_size=100*1024*1024):
    report=[]
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            normalized=item.filename.replace("\\","/")
            parts=PurePosixPath(normalized)
            flags=[]
            if parts.is_absolute() or ".." in parts.parts or (parts.parts and parts.parts[0].endswith(":")): flags.append("unsafe-path")
            ratio=item.file_size/max(item.compress_size,1)
            if ratio>max_ratio and item.file_size>1024*1024: flags.append("high-compression-ratio")
            if item.file_size>max_size: flags.append("large-entry")
            report.append({"name":item.filename,"compressed":item.compress_size,"uncompressed":item.file_size,"ratio":round(ratio,1),"flags":flags})
    return report
class Tests(unittest.TestCase):
    def test_safe_and_unsafe(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            with zipfile.ZipFile(tmp.name,"w") as z: z.writestr("safe/readme.txt","ok"); z.writestr("../escape.txt","bad")
            rows=audit(tmp.name); self.assertEqual(rows[0]["flags"],[]); self.assertIn("unsafe-path",rows[1]["flags"])
    def test_empty_archive(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            with zipfile.ZipFile(tmp.name,"w"): pass
            self.assertEqual(audit(tmp.name),[])
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("archive"); ap.add_argument("--json",action="store_true"); ap.add_argument("--max-ratio",type=float,default=1000); ap.add_argument("--max-mb",type=int,default=100); a=ap.parse_args()
    try: rows=audit(a.archive,a.max_ratio,a.max_mb*1024*1024)
    except (OSError,zipfile.BadZipFile) as exc: ap.error(str(exc))
    if a.json: print(json.dumps(rows,indent=2))
    else:
        for row in rows: print(f"{'⚠' if row['flags'] else '·'} {row['name']}  {row['uncompressed']} B  ratio {row['ratio']}  {','.join(row['flags'])}")
        print(f"{len(rows)} member(s)")
    raise SystemExit(any(r["flags"] for r in rows))
if __name__=="__main__":
    if "--self-test" in sys.argv: unittest.main(argv=[sys.argv[0]])
    else: main()
