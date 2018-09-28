#!/usr/bin/php
<?php

$liveDir = __DIR__ . '/live';
$backupsDir = "$liveDir-back";

try {
    if (!is_dir($backupsDir)) {
        mkdir($backupsDir, 0777, true);
    }
    if (!is_dir($currentBacupDir = $backupsDir . '/current')) {
        // first backup:
        execOrFail("rsync -aAHv '$liveDir/' '$currentBacupDir'");
    } else {
        // not first backup:
        // assert !E temp last dir:
        if (is_dir($tmpBackupDir = $backupsDir . '/tmp')) {
            // throw new Exception("tmp dir allready exists", 1);
            echo "[notice]\ttmp dir allready exists -> resuming previous backup operation\n";
        } else {
            // rename last backup (current) to temp:
            if (! rename($currentBacupDir, $tmpBackupDir)) {
                throw new Exception("cannot rename '$currentBacupDir' to '$tmpBackupDir'", 1);
            }
            // make new backup, hardlinking unchanged files from last backup (now in temp):
            execOrFail("rsync -aAHv '$liveDir/' '$currentBacupDir' --link-dest='$tmpBackupDir'");
        }
        // deleting unchanged (and now duplicated) in temp:
        execOrFail("find '$tmpBackupDir' -type f -links +1 -delete");
        execOrFail("find '$tmpBackupDir' -type d -empty -delete");
        // rename temp to last modified file timestamp:
        $lastTimestamp = execOrFail("find '$tmpBackupDir' -type f -printf '%TY-%Tm-%Td_%TH.%TM.%TS %p\n'|sort|tail -n 1|cut -d . -f 1-2");
        if (count($lastTimestamp)) {
            if (!is_dir($previousLast = $backupsDir . '/' . $lastTimestamp[0])) {
                mkdir($previousLast, 0777, true);
            }
            execOrFail("cp -r --backup=numbered $tmpBackupDir/* $previousLast");
            execOrFail("rm -r '$tmpBackupDir'");
        } else {
            echo "no new files since last backup\n";
        }
    }
} catch (Exception $e) {
    echo "Exception: " . $e->getMessage() . "\n";
    echo "Line: " . $e->getLine() . "\n";
    echo $e->getTraceAsString() . "\n";
}
echo "\n\n";

function execOrFail($command)
{
    echo "---------->\n";
    echo "$command\n";
    exec($command, $cmdOut, $cmdRetVal);
    if ($cmdRetVal) {
        throw new Exception("command '$command' returns $cmdRetVal", 1);
    }
    echo "\t" . implode("\n\t", $cmdOut) . "\n";
    return $cmdOut;
}
