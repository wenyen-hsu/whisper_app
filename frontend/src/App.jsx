import React, { useState } from 'react';
import { ThemeProvider, createTheme, CssBaseline, Container, Typography, Box, Paper, Button, Dialog, DialogTitle, DialogContent, DialogActions, FormGroup, FormControlLabel, Checkbox, Alert, LinearProgress } from '@mui/material';
import UploadArea from './components/UploadArea';
import useUpload from './hooks/useUpload';
import useRecorder from './hooks/useRecorder';

const darkTheme = createTheme({
  palette: { mode: 'dark' },
});

function downloadText(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

function App() {
  const { uploading, progress, result, error, upload } = useUpload();
  const [file, setFile] = useState(null);
  const [recDialogOpen, setRecDialogOpen] = useState(false);
  const [recBlob, setRecBlob] = useState(null);
  const [savePath, setSavePath] = useState('');
  const [downloadTxt, setDownloadTxt] = useState(true);
  const [downloadSrt, setDownloadSrt] = useState(true);
  const [status, setStatus] = useState('idle'); // idle, recording, uploading, transcribing, done
  const [recError, setRecError] = useState(''); // 新增錄音錯誤訊息
  const { recording, startRecording, stopRecording } = useRecorder(
    (blob) => {
      console.log('useRecorder onStop callback 被呼叫，blob:', blob, 'size:', blob.size);
      setRecBlob(blob);
      setRecDialogOpen(false);
      setStatus('uploading');
      upload(new File([blob], 'record.wav', { type: 'audio/wav' }), savePath, () => setStatus('transcribing'));
    },
    (errMsg) => {
      console.error('useRecorder onError callback 被呼叫:', errMsg);
      setRecError(errMsg);
      setRecDialogOpen(false);
      setStatus('idle');
    }
  );

  const handleFileAccepted = (file) => {
    console.log('handleFileAccepted 被呼叫，file:', file, 'size:', file?.size);
    setFile(file);
    setStatus('uploading');
    upload(file, savePath, () => setStatus('transcribing'));
  };

  const handleRecordClick = () => {
    console.log('點擊即時錄音');
    setRecDialogOpen(true);
    setStatus('recording');
    startRecording();
  };

  const handleStopRecording = () => {
    console.log('點擊停止錄音');
    stopRecording();
    setStatus('uploading');
  };

  // 狀態列顯示
  let statusText = '';
  if (status === 'recording') statusText = '錄音中...';
  else if (status === 'uploading') statusText = '上傳中...';
  else if (status === 'transcribing') statusText = '轉錄中...';
  else if (status === 'done') {
    if (result) {
      if (!result.text && !result.srt) statusText = '無辨識內容';
      else if (!result.text) statusText = '無辨識文字內容';
      else if (!result.srt) statusText = '無字幕內容';
      else statusText = '轉錄完成';
    } else {
      statusText = '轉錄完成';
    }
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="sm" sx={{ py: 6 }}>
        <Typography variant="h4" align="center" gutterBottom>Whisper 語音轉文字</Typography>
        {status !== 'idle' && (
          <Box sx={{ mb: 2 }}>
            <Alert severity={statusText.includes('無') ? 'warning' : 'info'}>{statusText}</Alert>
            {(status === 'uploading' || status === 'transcribing') && <LinearProgress sx={{ mt: 1 }} />}
          </Box>
        )}
        <UploadArea
          onFileAccepted={handleFileAccepted}
          uploading={uploading}
          progress={progress}
          onRecordClick={handleRecordClick}
          savePath={savePath}
          setSavePath={setSavePath}
        />
        <Dialog open={recDialogOpen} onClose={() => { setRecDialogOpen(false); stopRecording(); setStatus('idle'); }}>
          <DialogTitle>即時錄音</DialogTitle>
          <DialogContent>
            <Typography>{recording ? '錄音中... 請說話' : '錄音已停止'}</Typography>
            {recError && <Alert severity="error" sx={{ mt: 2 }}>{recError}</Alert>}
          </DialogContent>
          <DialogActions>
            {recording ? (
              <Button onClick={handleStopRecording} color="primary">停止錄音</Button>
            ) : (
              <Button onClick={() => { setRecDialogOpen(false); setStatus('idle'); setRecError(''); }} color="primary">關閉</Button>
            )}
          </DialogActions>
        </Dialog>
        {error && <Paper sx={{ mt: 2, p: 2, bgcolor: 'error.main', color: 'error.contrastText' }}>{error}</Paper>}
        {result && (
          <Box sx={{ mt: 4 }}>
            <FormGroup row sx={{ mb: 2 }}>
              <FormControlLabel
                control={<Checkbox checked={downloadTxt} onChange={e => setDownloadTxt(e.target.checked)} />}
                label="下載 TXT"
              />
              <FormControlLabel
                control={<Checkbox checked={downloadSrt} onChange={e => setDownloadSrt(e.target.checked)} />}
                label="下載 SRT"
              />
            </FormGroup>
            <Alert severity="info" sx={{ mb: 2 }}>
              下載檔案將由瀏覽器自動存到「下載」資料夾，或依您的瀏覽器設定彈出另存新檔視窗，無法直接指定本機任意資料夾。
            </Alert>
            <Typography variant="h6">純文字結果：</Typography>
            <Paper sx={{ p: 2, mb: 2, whiteSpace: 'pre-wrap' }}>{result.text}</Paper>
            {downloadTxt && (
              <Button
                variant="outlined"
                sx={{ mr: 2, mb: 2 }}
                onClick={() => downloadText('transcript.txt', result.text)}
                disabled={!result.text}
              >
                下載 TXT
              </Button>
            )}
            <Typography variant="h6">SRT 字幕：</Typography>
            <Paper sx={{ p: 2, whiteSpace: 'pre-wrap' }}>{result.srt}</Paper>
            {downloadSrt && (
              <Button
                variant="outlined"
                sx={{ mr: 2, mt: 1 }}
                onClick={() => downloadText('transcript.srt', result.srt)}
                disabled={!result.srt}
              >
                下載 SRT
              </Button>
            )}
          </Box>
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;
