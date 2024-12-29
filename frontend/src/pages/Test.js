import * as React from 'react';
import {Box, Typography,Button, List, ListItem, ListItemText, IconButton } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import { styled } from '@mui/material/styles';
import { useState } from 'react';
import axios from 'axios';

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

export default function Test() {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // 文件上传
  const handleFileChange = (event) => {
    const selectedFiles = event.target.files;
    const newFiles = Array.from(selectedFiles);
    setFiles(newFiles);
    console.log(files);
    files.forEach(file => {
      console.log(file);
      const formData = new FormData();
      formData.append('file', file);
      axios.post('api/uploadfile', formData)
       .then((res) => {
        setUploadedFiles(prevFiles => [...prevFiles, file]);
        console.log(res);
      }).catch((err) => {
        console.error(err);
      });
    });
    setFiles([]);
    //console.log(files);
  };

  const handleFileUpload = () => {
    console.log(123);
    files.forEach(file => {
      console.log(123);
      const formData = new FormData();
      formData.append('file', file);
      axios.post('api/uploadfile', formData)
       .then((res) => {
        setUploadedFiles(prevFiles => [...prevFiles, file]);
        console.log(res);
      }).catch((err) => {
        console.error(err);
      });
    });
    setFiles([]);
  }

  const handleFileDelete = (fileName) => {
    setUploadedFiles(prevFiles => prevFiles.filter(file => file.name !== fileName));
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
        >
          Upload files
          <VisuallyHiddenInput
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            multiple
          />
        </Button>

        {uploadedFiles.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
              已上传的文件：
            </Typography>
            <List>
              {uploadedFiles.map((file) => (
                <ListItem key={file.name} sx={{ display: 'flex', alignItems: 'center' }}>
                  <ListItemText primary={file.name} />
                  <IconButton onClick={() => handleFileDelete(file.name)}>
                    <DeleteIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          </Box>
        )}
    </div>
  );
}