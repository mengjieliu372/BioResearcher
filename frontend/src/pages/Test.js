import React, { useState } from 'react';
import { Button, CircularProgress, Typography } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { styled } from '@mui/system';

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const FileUpload = () => {
  const [loading, setLoading] = useState(false); // 总的加载状态
  const [files, setFiles] = useState([]); // 存储已选择的文件以及它们的状态

  // 处理文件变化并上传
  const handleFileChange = async (event) => {
    const selectedFiles = event.target.files;
    
    if (selectedFiles.length > 0) {
      // 更新文件列表及其状态
      const newFiles = Array.from(selectedFiles).map(file => ({
        name: file.name,
        status: '正在上传', // 初始状态为“正在上传”
        file,
      }));
      
      setFiles(prevFiles => [...prevFiles, ...newFiles]); // 将新文件加入到当前文件列表中
      setLoading(true); // 设置总的加载状态为 true，禁用上传按钮

      try {
        // 遍历文件并上传
        await Promise.all(
          newFiles.map(async (fileObj, index) => {
            const formData = new FormData();
            formData.append('file', fileObj.file);

            try {
              const response = await fetch('your-upload-endpoint', {
                method: 'POST',
                body: formData,
              });

              // 如果上传成功，更新状态
              if (response.ok) {
                const updatedFiles = [...files];
                updatedFiles[index].status = '上传完成'; // 更新对应文件的状态为“上传完成”
                setFiles(updatedFiles);
              } else {
                throw new Error(`文件 ${fileObj.name} 上传失败`);
              }
            } catch (error) {
              const updatedFiles = [...files];
              updatedFiles[index].status = `上传失败: ${error.message}`;
              setFiles(updatedFiles);
            }
          })
        );
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false); // 上传完成，停止总的加载状态
      }
    }
  };

  return (
    <div>
      <Button
        component="label"
        role={undefined}
        variant="contained"
        tabIndex={-1}
        startIcon={<CloudUploadIcon />}
        sx={{ mb: 2 }}
        disabled={loading} // 禁用按钮如果正在加载
      >
        {loading ? '上传中...' : '上传文件'}
        <VisuallyHiddenInput
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          multiple
        />
      </Button>

      {/* 显示文件列表及其状态 */}
      <div>
        {files.map((fileObj, index) => (
          <div key={index} style={{ marginBottom: 8 }}>
            <Typography variant="body2">
              {fileObj.name} - {fileObj.status}
            </Typography>
            {fileObj.status === '正在上传' && <CircularProgress size={20} />}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileUpload;
