IDENTIFICATION DIVISION.
PROGRAM-ID. SORT-TEAMS.

ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT IN-FILE ASSIGN TO "teams_in.txt"
        ORGANIZATION IS LINE SEQUENTIAL.
    SELECT WORK-FILE ASSIGN TO "sortwork.tmp".
    SELECT TEMP-FILE ASSIGN TO "sort_temp.tmp"
        ORGANIZATION IS LINE SEQUENTIAL.
    SELECT OUT-FILE ASSIGN TO "teams_sorted.txt"
        ORGANIZATION IS LINE SEQUENTIAL.

DATA DIVISION.
FILE SECTION.
FD  IN-FILE.
01  IN-REC                  PIC X(19).

SD  WORK-FILE.
01  WORK-REC.
    05 W-ABBR               PIC X(03).
    05 W-DIV                PIC X(01).
    05 W-GP                 PIC 9(02).
    05 W-WINS               PIC 9(02).
    05 W-LOSSES             PIC 9(02).
    05 W-OTL                PIC 9(02).
    05 W-PTS                PIC 9(03).
    05 W-RW                 PIC 9(02).
    05 W-ROW                PIC 9(02).

FD  TEMP-FILE.
01  TEMP-REC.
    05 T-BASE.
        10 T-ABBR           PIC X(03).
        10 T-DIV            PIC X(01).
        10 T-GP             PIC 9(02).
        10 T-WINS           PIC 9(02).
        10 T-LOSSES         PIC 9(02).
        10 T-OTL            PIC 9(02).
        10 T-PTS            PIC 9(03).
    05 T-RW                 PIC 9(02).
    05 T-ROW                PIC 9(02).

FD  OUT-FILE.
01  OUT-REC.
    05 O-BASE               PIC X(15).
    05 O-SEED               PIC X(03).
    05 O-RW                 PIC 9(02).
    05 O-ROW                PIC 9(02).

WORKING-STORAGE SECTION.
01  WS-EOF                  PIC X(01) VALUE "N".
01  WS-RANK                 PIC 9(02) VALUE 0.
01  WS-CNT-A                PIC 9(01) VALUE 0.
01  WS-CNT-M                PIC 9(01) VALUE 0.
01  WS-CNT-C                PIC 9(01) VALUE 0.
01  WS-CNT-P                PIC 9(01) VALUE 0.
01  WS-WC-E                 PIC 9(01) VALUE 0.
01  WS-WC-W                 PIC 9(01) VALUE 0.

PROCEDURE DIVISION.
MAIN-PARA.
    SORT WORK-FILE
        ON DESCENDING KEY W-PTS
        ON ASCENDING  KEY W-GP
        ON DESCENDING KEY W-RW
        ON DESCENDING KEY W-ROW
        ON DESCENDING KEY W-WINS
        USING IN-FILE
        GIVING TEMP-FILE.

    OPEN INPUT TEMP-FILE
         OUTPUT OUT-FILE.

    DISPLAY "=== OFFICIAL NHL PLAYOFF SEEDING (COBOL + RW/ROW) ===".
    PERFORM UNTIL WS-EOF = "Y"
        READ TEMP-FILE
            AT END
                MOVE "Y" TO WS-EOF
            NOT AT END
                ADD 1 TO WS-RANK
                MOVE T-BASE TO O-BASE
                MOVE T-RW   TO O-RW
                MOVE T-ROW  TO O-ROW
                PERFORM ASSIGN-SEED-PARA
                WRITE OUT-REC
                DISPLAY WS-RANK ". " T-ABBR " (" T-DIV ") - "
                        T-PTS " PTS | RW:" T-RW " ROW:" T-ROW
                        "  [" O-SEED "]"
        END-READ
    END-PERFORM.

    CLOSE TEMP-FILE OUT-FILE.
    STOP RUN.

ASSIGN-SEED-PARA.
    MOVE "---" TO O-SEED
    EVALUATE T-DIV
        WHEN "A"
            IF WS-CNT-A < 3
                ADD 1 TO WS-CNT-A
                STRING "A" WS-CNT-A " " DELIMITED BY SIZE INTO O-SEED
            ELSE
                PERFORM CHECK-EAST-WC
            END-IF
        WHEN "M"
            IF WS-CNT-M < 3
                ADD 1 TO WS-CNT-M
                STRING "M" WS-CNT-M " " DELIMITED BY SIZE INTO O-SEED
            ELSE
                PERFORM CHECK-EAST-WC
            END-IF
        WHEN "C"
            IF WS-CNT-C < 3
                ADD 1 TO WS-CNT-C
                STRING "C" WS-CNT-C " " DELIMITED BY SIZE INTO O-SEED
            ELSE
                PERFORM CHECK-WEST-WC
            END-IF
        WHEN "P"
            IF WS-CNT-P < 3
                ADD 1 TO WS-CNT-P
                STRING "P" WS-CNT-P " " DELIMITED BY SIZE INTO O-SEED
            ELSE
                PERFORM CHECK-WEST-WC
            END-IF
    END-EVALUATE.

CHECK-EAST-WC.
    IF WS-WC-E < 2
        ADD 1 TO WS-WC-E
        STRING "WC" WS-WC-E DELIMITED BY SIZE INTO O-SEED
    END-IF.

CHECK-WEST-WC.
    IF WS-WC-W < 2
        ADD 1 TO WS-WC-W
        STRING "WC" WS-WC-W DELIMITED BY SIZE INTO O-SEED
    END-IF.