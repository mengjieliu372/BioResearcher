import * as React from 'react';
import { useState } from 'react';
import { Container, Box, TextField, Typography, FormGroup, FormControlLabel, Checkbox, Radio, RadioGroup, FormControl, Button, List, ListItem, ListItemText, IconButton } from '@mui/material';
import Grid from '@mui/material/Grid2';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';

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

export default function NewProject() {
  const [value1, setValue1] = useState('');
  const [value2, setValue2] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleInput1 = (event) => {
    const newValue = event.target.value.replace(/[^0-9]/g, '');
    setValue1(newValue);
  };

  const handleInput2 = (event) => {
    const newValue = event.target.value.replace(/[^0-9]/g, '');
    setValue2(newValue);
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    setUploadedFiles(prevFiles => [...prevFiles, ...files]);
  };

  const handleFileDelete = (fileName) => {
    setUploadedFiles(prevFiles => prevFiles.filter(file => file.name !== fileName));
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Container
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          width: '60%',
          maxWidth: 800,
          backgroundColor: 'white',
          borderRadius: 8,
          padding: 4,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
          p: 4,
          mb: 8,
        }}
      >
        <Typography variant="h4" sx={{ mb: 4, fontWeight: 'bold', color: '#333' }}>
          Create a New Project
        </Typography>

        <Grid container spacing={2}>
          <Grid item size={12}>
            <TextField
              label="实验名称"
              variant="outlined"
              required
              fullWidth
              sx={{ mb: 2 }}
            />
          </Grid>

          <Grid item size={12}>
            <TextField
              label="实验目的"
              variant="outlined"
              required
              fullWidth
              sx={{ mb: 2 }}
            />
          </Grid>

          <Grid item size={12}>
            <TextField
              label="实验条件"
              variant="outlined"
              required
              multiline
              fullWidth
              rows={3}
              sx={{ mb: 2 }}
            />
          </Grid>

          <Grid item size={12}>
            <TextField
              label="实验要求"
              variant="outlined"
              required
              multiline
              fullWidth
              rows={3}
              sx={{ mb: 2 }}
            />
          </Grid>
        </Grid>

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mt: 4 }}>
          选择要检索的数据库
        </Typography>

        <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
          文献库：
        </Typography>
        <FormGroup row sx={{ mb: 2 }}>
          <FormControlLabel control={<Checkbox defaultChecked />} label="PMC" />
          <FormControlLabel control={<Checkbox />} label="PubMed" />
        </FormGroup>

        <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
          数据集库：
        </Typography>
        <FormGroup row sx={{ mb: 2 }}>
          <FormControlLabel control={<Checkbox defaultChecked />} label="GEO" />
          <FormControlLabel control={<Checkbox />} label="NCBI" />
          <FormControlLabel control={<Checkbox />} label="cBioPortal" />
        </FormGroup>

        <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
          本地文献：
        </Typography>
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

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}>
          LLM模型选择
        </Typography>

        <FormControl>
          <RadioGroup
            row
            defaultValue="GPT4o"
            aria-labelledby="llm"
            name="row-radio-buttons-group"
            sx={{ mb: 4 }}
          >
            <FormControlLabel value="GPT4o" control={<Radio />} label="GPT4o" />
            <FormControlLabel value="gemini" control={<Radio />} label="gemini" />
            <FormControlLabel value="claude" control={<Radio />} label="claude" />
          </RadioGroup>
        </FormControl>

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}>
          其他可选参数
        </Typography>

        <Grid container spacing={2}>
          <Grid item size={6}>
            <TextField
              label="参考文献的数量"
              variant="outlined"
              value={value1}
              onInput={handleInput1}
              fullWidth
            />
          </Grid>
          <Grid item size={6}>
            <TextField
              label="Reviewer最大轮次"
              variant="outlined"
              value={value2}
              onInput={handleInput2}
              fullWidth
            />
          </Grid>
        </Grid>

        <Button
          variant="contained"
          color="primary"
          size="large"
          sx={{ mt: 4 }}
        >
          提交
        </Button>
      </Container>
    </Box>
  );
}
