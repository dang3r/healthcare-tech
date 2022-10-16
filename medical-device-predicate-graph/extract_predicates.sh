#!/usr/bin/env bash
#
# Extract device predicates from FDA device summary PDFs

TEXT_DIRECTORY="$1"

find text -name '*.pdf.txt' | {
    # Extract all device-like names from the text
    # Eg. K123312, DEN132123
    xargs -P 1 pcregrep -o1 '((K|DEN|P|PMA)\d{5,})'
} | {
    # Pcregrp outputs the filename and the matching text
    # eg. text/text/K101715.pdf.txt:K101715
    # Extract only the device id, and the predicate device is
    pcregrep -o1 -o2 --om-separator=',' '([A-Za-z0-9]*).pdf.txt:(.*)' > edges.txt
} 