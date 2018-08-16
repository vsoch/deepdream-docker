#!/usr/bin/env python

from PIL import Image
import argparse
import os
import sys

# -- Argument Parsing
def get_parser():
    parser = argparse.ArgumentParser(description="DeepDream Dimension Helper")

    parser.add_argument('--image', dest="image", 
                        help="image to get dimensions for", 
                        default=None, type=str)

    parser.add_argument('--width', dest='width', action='store_true',
                        help='only print width',
                        default=False)

    parser.add_argument('--height', dest='height', action='store_true',
                        help='only print height',
                        default=False)

    return parser



def main():

    parser = get_parser()

    try:
        args = parser.parse_args()
    except:
        sys.exit(0)

    if not os.path.exists(args.image):
        print('Cannot find %s' % args.image)

    im = Image.open(args.image)

    if args.width is True:
        print(im.size[0])
    elif args.height is True:
        print(im.size[1])
    else:
        print(im.size)


if __name__ == '__main__':
    main()
