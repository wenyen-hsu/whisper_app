import { useState } from 'react';
import { uploadAudio } from '../services/api';

const useUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 新增 savePath 參數
  const upload = async (file, savePath) => {
    console.log('[useUpload] upload called, file:', file, 'savePath:', savePath);
    setUploading(true);
    setProgress(0);
    setError(null);
    setResult(null);
    console.log('[useUpload] 準備上傳檔案:', file, 'size:', file?.size);
    try {
      const response = await uploadAudio(file, savePath, (e) => {
        if (e.total) {
          const prog = Math.round((e.loaded * 100) / e.total);
          console.log('[useUpload] setProgress:', prog);
          setProgress(prog);
        }
      });
      console.log('[useUpload] API 回傳 response:', response);
      if (response && response.data) {
        console.log('[useUpload] setResult 呼叫, response.data:', response.data);
        setResult({
          ...response.data.data,
          saved_files: response.data.saved_files
        });
      } else {
        console.log('[useUpload] setError 呼叫, response 無 data');
        setError('API 回傳格式錯誤');
      }
    } catch (err) {
      // 更詳細的錯誤訊息顯示
      if (err.response) {
        console.log('[useUpload] setError 呼叫, 伺服器錯誤:', err.response);
        setError(
          `伺服器錯誤 (${err.response.status}): ` +
          (err.response.data?.message || JSON.stringify(err.response.data))
        );
      } else if (err.request) {
        console.log('[useUpload] setError 呼叫, 無法連線到伺服器');
        setError('無法連線到伺服器，請確認後端 API 是否啟動');
      } else {
        console.log('[useUpload] setError 呼叫, 未知錯誤:', err.message);
        setError('未知錯誤: ' + err.message);
      }
    } finally {
      console.log('[useUpload] setUploading(false)');
      setUploading(false);
    }
  };

  return { uploading, progress, result, error, upload };
};

export default useUpload;
