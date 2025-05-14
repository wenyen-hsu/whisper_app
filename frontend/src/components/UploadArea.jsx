import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, LinearProgress, Paper, Button, TextField } from '@mui/material';

const UploadArea = ({ onFileAccepted, uploading, progress, onRecordClick, savePath, setSavePath }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileAccepted(acceptedFiles[0]);
    }
  }, [onFileAccepted]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/wav': ['.wav'],
      'audio/mp3': ['.mp3'],
      'audio/mpeg': ['.mp3'],
      'video/mp4': ['.mp4'],
      'audio/mp4': ['.mp4'],
      'audio/x-m4a': ['.m4a'],
      'audio/m4a': ['.m4a'],
      'audio/webm': ['.webm']
    },
    maxSize: 500 * 1024 * 1024
  });

  return (
    <Paper {...getRootProps()} sx={{ p: 4, textAlign: 'center', bgcolor: 'background.default', border: '2px dashed', borderColor: isDragActive ? 'primary.main' : 'grey.500', cursor: 'pointer' }}>
      <input {...getInputProps()} />
      <Typography variant="h6" color="text.secondary">
        {isDragActive ? '放開檔案以上傳' : '拖曳或點擊以上傳音訊/影片檔案 (WAV/MP3/MP4/M4A, 500MB 以內)'}
      </Typography>
      <Button variant="contained" color="primary" sx={{ mt: 2 }} onClick={e => { e.stopPropagation(); onRecordClick && onRecordClick(); }}>
        即時錄音
      </Button>
      {uploading && <Box sx={{ mt: 2 }}><LinearProgress variant="determinate" value={progress} /></Box>}
    </Paper>
  );
};

export default UploadArea;
