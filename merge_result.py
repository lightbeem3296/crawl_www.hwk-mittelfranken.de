import json
import os
import sys
import traceback

import numpy as np
import pandas as pd


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
        dst_fpath = os.path.join(dst_dpath, f"{src_dname}")

        res0_df = pd.DataFrame(
            {
                "name": [],
                "address": [],
                "email": [],
                "telephone": [],
                "mobile": [],
                "fax": [],
            }
        )
        res1_df = pd.DataFrame(
            {
                "email": [],
            }
        )
        res2_df = pd.DataFrame(
            {
                "name": [],
                "address": [],
                "telephone": [],
                "mobile": [],
                "fax": [],
            }
        )

        print(f"[*] merge: {src_dpath} > {dst_fpath}.*")
        for dpath, _, fnames in os.walk(src_dpath):
            sorted_fnames = sorted(fnames, key=natural_sort_key)
            for fname in sorted_fnames:
                if fname.lower().endswith(".json"):
                    fpath = os.path.join(dpath, fname)
                    print(f"[*] filepath: {fpath[len(src_dpath):]}")

                    with open(fpath, mode="r") as f:
                        info = json.load(f)
                        res0_df = pd.concat([res0_df, pd.DataFrame([info])], ignore_index=True)
                        res1_df = pd.concat(
                            [
                                res1_df,
                                pd.DataFrame(
                                    [
                                        {
                                            "email": info["email"],
                                        }
                                    ]
                                ),
                            ],
                            ignore_index=True,
                        )
                        res2_df = pd.concat(
                            [
                                res2_df,
                                pd.DataFrame(
                                    [
                                        {
                                            "name": info["name"],
                                            "address": info["address"],
                                            "telephone": info["telephone"],
                                            "mobile": info["mobile"],
                                            "fax": info["fax"],
                                        }
                                    ]
                                ),
                            ],
                            ignore_index=True,
                        )
        res0_df.to_excel(dst_fpath+"_0.xlsx", index=False)
        res1_df.to_excel(dst_fpath+"_1.xlsx", index=False)
        res2_df.to_excel(dst_fpath+"_2.xlsx", index=False)
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
