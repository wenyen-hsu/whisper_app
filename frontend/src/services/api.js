import axios from 'axios';

export const uploadAudio = async (file, savePath, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  console.log('[uploadAudio] 準備送出 /api/transcribe 請求, file:', file, 'savePath:', savePath);
  try {
    const response = await axios.post('/api/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
    console.log('[uploadAudio] 收到 response:', response);
    return response;
  } catch (err) {
    console.error('[uploadAudio] 發生錯誤:', err);
    throw err;
  } finally {
    console.log('[uploadAudio] 請求結束');
  }
};

export const fetchServerDirs = async (base = 'uploads/') => {
  const res = await axios.get('/api/list_dirs', { params: { base } });
  return res.data.dirs;
};
