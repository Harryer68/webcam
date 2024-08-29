import os
import shutil
import time
from flask import Flask, render_template
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

app = Flask(__name__)

# 다운로드 폴더와 이동할 폴더 경로 설정
download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
destination_folder = "C:\\video"
downloaded_files = {}  # 다운로드 중인 파일 이름을 추적하기 위한 딕셔너리

class MoveFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:  # 디렉토리가 아닐 경우
            original_file_name = os.path.basename(event.src_path)
            file_extension = os.path.splitext(original_file_name)[1]  # 파일 확장자 추출
            print(f"새 파일 발견: {original_file_name}")

            # .tmp 파일일 경우 대기
            if file_extension.lower() == '.tmp':
                print(f"{original_file_name}은(는) 다운로드 중입니다. 대기 중...")
                downloaded_files[original_file_name] = event.src_path  # 파일 이름과 경로 저장
                
                # .tmp 파일이 존재하는 동안 대기
                while os.path.exists(event.src_path):
                    time.sleep(1)  # 1초 대기

                # 다운로드가 완료된 후 관련된 .webm 파일 찾기
                tmp_base_name = os.path.splitext(original_file_name)[0]  # .tmp 확장자를 제외한 파일 이름
                webm_file_name = f"recorded_video_{tmp_base_name}.webm"
                new_file_path = os.path.join(download_folder, webm_file_name)

                # .webm 파일이 존재하면 이동
                if os.path.exists(new_file_path):
                    destination_path = os.path.join(destination_folder, webm_file_name)
                    shutil.move(new_file_path, destination_path)
                    print(f"{webm_file_name}을(를) {destination_path}로 이동했습니다.")
                else:
                    print(f"{webm_file_name}이(가) 생성되지 않았습니다.")
                
                del downloaded_files[original_file_name]  # 다운로드 완료 후 딕셔너리에서 삭제

            elif file_extension.lower() == '.webm' and original_file_name.startswith("recorded_video_"):
                # 이미 "recorded_video_"로 시작하는 .webm 파일인 경우 바로 이동
                destination_path = os.path.join(destination_folder, original_file_name)
                shutil.move(event.src_path, destination_path)
                print(f"{original_file_name}을(를) {destination_path}로 이동했습니다.")
            else:
                print(f"{original_file_name}은(는) 처리할 파일이 아니므로 무시합니다.")

def start_file_watcher():
    # 이동할 폴더가 존재하지 않으면 생성
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    event_handler = MoveFileHandler()
    observer = Observer()
    observer.schedule(event_handler, download_folder, recursive=False)

    print(f"{download_folder}를 모니터링 중입니다...")
    observer.start()

    try:
        while True:
            time.sleep(1)  # CPU 사용량을 줄이기 위해 1초 대기
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # 파일 감시를 별도의 스레드에서 실행
    watcher_thread = threading.Thread(target=start_file_watcher, daemon=True)
    watcher_thread.start()
    
    app.run(debug=True)
