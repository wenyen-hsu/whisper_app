import { useState, useRef } from 'react';

const useRecorder = (onStop, onError) => {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      let mimeType = '';
      if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else {
        mimeType = 'audio/wav';
      }
      mediaRecorderRef.current = new window.MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        console.log('錄音結束，產生的 blob:', blob, 'size:', blob.size);
        // 關閉所有 audio track，釋放麥克風
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        if (blob.size === 0) {
          if (onError) onError('錄音失敗，沒有取得音訊資料');
          return;
        }
        onStop(blob);
      };
      mediaRecorderRef.current.onerror = (event) => {
        if (onError) onError('錄音過程發生錯誤: ' + event.error?.message);
      };
      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      console.error('錄音啟動失敗:', err);
      if (onError) onError('無法啟動錄音，請檢查麥克風權限: ' + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  return { recording, startRecording, stopRecording };
};

export default useRecorder;
