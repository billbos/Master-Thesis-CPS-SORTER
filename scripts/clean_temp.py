import os, shutil
import time
from pathlib import Path

if __name__ == '__main__':
    folder = 'C:/Users/bboss/AppData/Local/Temp'
    while True:
        now = time.time()
        count_removed = 0
        for filename in os.listdir(folder):
            try:
                file_path = os.path.join(folder, filename)
                if os.stat(file_path).st_mtime < now - 60:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        if not file_path.split('.')[-1] == 'model':
                            os.unlink(file_path)
                    # elif os.path.isdir(file_path):
                    #     shutil.rmtree(file_path)
                    count_removed += 1
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        print('finished_cleaning time: {}, removed_files {}'.format(now, count_removed))
        time.sleep(300)

