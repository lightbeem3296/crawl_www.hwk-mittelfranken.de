import json
import pandas as pd
import os
import traceback
import sys


def natural_sort_key(s):
    """
    Provides a sort key for strings that may or may not lead with an integer.
    """
    for i, c in enumerate(s):
        if not c.isdigit():
            break
    if not i:
        return s, 0
    else:
        return s[i:], int(s[:i])


def merge(src_dpath: str):
    try:
        if not os.path.isdir(src_dpath):
            print(f"[-] not directory: {src_dpath}")

        dst_dpath = os.path.dirname(src_dpath)
        src_dname = os.path.basename(src_dpath)
        dst_fpath = os.path.join(dst_dpath, f"{src_dname}.xlsx")

        result_df = pd.DataFrame()

        print(f"[*] merge: {src_dpath} > {dst_fpath}")
        for dpath, _, fnames in os.walk(src_dpath):
            sorted_fnames = sorted(fnames, key=natural_sort_key)
            for fname in sorted_fnames:
                if fname.lower().endswith(".json"):
                    fpath = os.path.join(dpath, fname)
                    print(f"[*] filepath: {fpath[len(src_dpath):]}")

                    with open(fpath, mode="r") as f:
                        info = json.load(f)
                        df = pd.read_excel(fpath)
                        result_df = pd.concat([result_df, df])

        result_df.to_excel(dst_fpath, index=False)
    except:
        traceback.print_exc()


def main():
    try:
        if len(sys.argv) > 1:
            src_dlist = sys.argv[1:]
            for src_dir in src_dlist:
                print(f"[*] src_dir: {src_dir}")
            for src_dir in src_dlist:
                merge(src_dir)
    except:
        traceback.print_exc()


if __name__ == "__main__":
    main()
