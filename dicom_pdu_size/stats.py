import glob

import pandas as pd

def main() -> None:
    fnames = glob.glob("*B.txt")
    fnames = sorted(fnames, key=lambda x: int(x[:-4].replace("KB", "000").replace("MB", "000000")))
    for fname in fnames:
        size = fname[:-4]
        df = pd.read_csv(fname, names=["StartTime", "EndTime"], sep=" ")
        df["RequestTime"] = df["EndTime"] - df["StartTime"]
        df = df.round(2)
        _mean = df["RequestTime"].mean().round(2) 
        _max = df["RequestTime"].max()
        _min = df["RequestTime"].min()

        df["RequestTime"].to_csv("{}_request_times.txt".format(size), index=False)
        print("{:6} : mean={:04}s min={:04}s max={:04}s".format(size, _mean, _min, _max))

if __name__ == "__main__":
    main()
