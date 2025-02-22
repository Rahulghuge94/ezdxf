# Purpose: test copy dxf file
# Copyright (c) 2011-2021, Manfred Moitzi
# License: MIT License
import sys
import time
import ezdxf


def copydxf(fromfile, tofile):
    starttime = time.time()
    doc = ezdxf.readfile(fromfile)
    doc.saveas(tofile)
    endtime = time.time()
    print(f"copy time: {endtime - starttime:.2f} seconds")


if __name__ == "__main__":
    copydxf(sys.argv[1], sys.argv[2])
