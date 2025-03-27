import * as React from 'react';
import { useState } from 'react';
import { Container, Box, TextField, Typography, FormGroup, FormControlLabel, Checkbox, Radio, RadioGroup, FormControl, Button, List, ListItem, ListItemText, IconButton } from '@mui/material';
import Grid from '@mui/material/Grid2';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import { addProject } from '../services/api';
import { uploadFile, deleteFile } from '../services/api';
import { useEffect } from 'react';

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
  const [expName, setExpName] = useState('');
  const [expPurpose, setExpPurpose] = useState('');
  const [expCondition, setExpCondition] = useState('');
  const [expRequirement, setExpRequirement] = useState('');
  const [paperset, setPaperset] = useState({ PMC: true, PubMed: false });
  const [dataset, setDataset] = useState({ GEO: true, NCBI: false, cBioPortal: false });
  const [llmModel, setLLMModel] = useState('GPT4o');
  const [framework, setFramework] = useState('BioResearch');
  const [refNum, setRefNum] = useState('');
  const [reviewerRound, setReviewerRound] = useState('');
  const [files, setFiles] = useState([]);

  const handleInputRefNum = (event) => {
    const newValue = event.target.value.replace(/[^0-9]/g, '');
    setRefNum(newValue);
  };

  const handleInputReviewerRound = (event) => {
    const newValue = event.target.value.replace(/[^0-9]/g, '');
    setReviewerRound(newValue);
  };

  const handlePaperChange = (event) => {
    setPaperset(prev => ({
      ...prev,
      [event.target.name]: event.target.checked
    }));
  };

  const handleDatabaseChange = (event) => {
    setDataset(prev => ({
      ...prev,
      [event.target.name]: event.target.checked
    }));
  };

  // 文件上传
  const handleFileChange = (event) => {
    const selectedFiles = event.target.files;
    if (selectedFiles.length > 0) {
      const newFiles = Array.from(selectedFiles).map(file => ({
        name: file.name,
        status: 'Uploading',
        file,
      }));
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
    };
  };

  useEffect(() => {
    const uploadingFiles = files.filter(file => file.status === 'Uploading');
    if (uploadingFiles.length > 0) {
      uploadingFiles.forEach((fileObj, index) => {
        if (fileObj.status === 'Uploaded' || fileObj.status === 'Failed')
          return;
        const formData = new FormData();
        formData.append('file', fileObj.file);

        uploadFile(formData).then((res) => {
          setFiles(prevFiles =>
            prevFiles.map((file, i) => {
              if (file.name === fileObj.name) {
                return {
                  ...file,
                  status: res.status === 200 ? 'Uploaded' : 'Failed',
                };
              }
              return file;
            })
          );
        });
      });
    }
  }, [files.length]);



  const handleFileDelete = (fileName) => {
    deleteFile(fileName);
    const newFiles = files.filter(file => file.name !== fileName);
    setFiles(newFiles);
  };

  const handleLlmModelChange = (event) => {
    setLLMModel(event.target.value);
  };

  const handleFrameworkChange = (event) => {
    setFramework(event.target.value);
  };

  const handleSubmit = () => {
    // 数据验证
    if (!expName || !expPurpose || !expCondition || !expRequirement) {
      alert('请填写实验相关信息！');
      return;
    }

    // 检查paperset和dataset是否全为false
    if (!Object.values(paperset).some(Boolean)) {
      alert('请选择要检索的文献库！');
      return;
    }
    if (!Object.values(dataset).some(Boolean)) {
      alert('请选择要检索的数据集库！');
      return;
    }

    // 检查文件是否上传完成
    if (files.some(file => file.status !== 'Uploaded')) {
      alert('文件上传中，请稍后提交！');
      return;
    }
    const refNumInt = parseInt(refNum);
    const reviewerRoundInt = parseInt(reviewerRound);
    const id = 0;
    const formData = {
      id,
      expName,
      expPurpose,
      expCondition,
      expRequirement,
      paperset,
      dataset,
      llmModel,
      framework,
      refNum: refNumInt,
      reviewerRound: reviewerRoundInt,
      fileNames: files.map(file => file.name)
    };

    // 上传项目信息
    addProject(formData).then((res) => {
      if (res.status === 200) {
        alert('项目创建成功！');
      }
      else {
        alert('创建失败，请重试！');
      }
    });
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          width: '55vw',
          backgroundColor: 'white',
          borderRadius: 3,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
          pl: 3,
          pr: 3,
          pt: 2,
          mb: 4,
        }}
      >
        <Typography variant="h4" sx={{ mb: 2, fontWeight: 'bold', color: '#333' }}>
          Create a New Project
        </Typography>
        <Grid container spacing={2}>
          <Grid item="true" size={12}>
            <TextField
              label="Experiment Name"
              variant="outlined"
              required
              fullWidth
              sx={{ mb: 2 }}
              value={expName}
              onChange={(e) => setExpName(e.target.value)}
            />
          </Grid>

          <Grid item="true" size={12}>
            <TextField
              label="Experiment Purpose"
              variant="outlined"
              required
              fullWidth
              sx={{ mb: 2 }}
              value={expPurpose}
              onChange={(e) => setExpPurpose(e.target.value)}
            />
          </Grid>

          <Grid item="true" size={12}>
            <TextField
              label="Experiment Condition"
              variant="outlined"
              required
              multiline
              fullWidth
              rows={3}
              sx={{ mb: 2 }}
              value={expCondition}
              onChange={(e) => setExpCondition(e.target.value)}
            />
          </Grid>

          <Grid item="true" size={12}>
            <TextField
              label="Experiment Requirement"
              variant="outlined"
              required
              multiline
              fullWidth
              rows={3}
              sx={{ mb: 2 }}
              value={expRequirement}
              onChange={(e) => setExpRequirement(e.target.value)}
            />
          </Grid>
        </Grid>



        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mt: 1 }}>
          Select the database to search
        </Typography>
        <Typography variant="h6" sx={{ color: '#555'}}>
          Paper database:
        </Typography>
        <FormGroup row>
          <FormControlLabel
            control={<Checkbox checked={paperset.PMC} onChange={handlePaperChange} name='PMC' />}
            label="PMC" />
          <FormControlLabel
            control={<Checkbox checked={paperset.PubMed} onChange={handlePaperChange} name='PubMed' />}
            label="PubMed" />
        </FormGroup>
        <Typography variant="h6" sx={{ color: '#555'}}>
          Dataset database:
        </Typography>
        <FormGroup row >
          <FormControlLabel
            control={<Checkbox checked={dataset.GEO} onChange={handleDatabaseChange} name='GEO' />}
            label="GEO" />
          <FormControlLabel
            control={<Checkbox checked={dataset.NCBI} onChange={handleDatabaseChange} name='NCBI' />}
            label="NCBI" />
          <FormControlLabel
            control={<Checkbox checked={dataset.cBioPortal} onChange={handleDatabaseChange} name='cBioPortal' />}
            label="cBioPortal" />
        </FormGroup>

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333' }}>
          Upload local papers
        </Typography>
        <Button
          component="label"
          role={undefined}
          variant="contained"
          tabIndex={-1}
          startIcon={<CloudUploadIcon />}
          sx={{ m: 2 }}
        >
          Upload files
          <VisuallyHiddenInput
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            multiple
          />
        </Button>

        {files.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ color: '#555', mb: 0.5 }}>
              Files selected:
            </Typography>
            <List>
              {files.map((file, index) => (
                <ListItem sx={{ display: 'flex', alignItems: 'center', p: 1, borderRadius: 1, bgcolor: 'background.default', mb: 1 }}>
                  {/* 文件名称 */}
                  <ListItemText
                    primary={file.name}
                    primaryTypographyProps={{
                      variant: 'body1',
                      sx: { color: 'text.primary' },
                    }}
                  />

                  <Typography
                    sx={{
                      ml: 2,
                      mr: 2,
                    }}
                  >
                    {file.status}
                  </Typography>
                  <IconButton onClick={() => handleFileDelete(file.name)} sx={{ color: 'error.main' }}>
                    <DeleteIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333'}}>
          LLM model selection
        </Typography>

        <FormControl>
          <RadioGroup
            row
            defaultValue="GPT4o"
            aria-labelledby="llm"
            onChange={handleLlmModelChange}
            name="row-radio-buttons-group"
          >
            <FormControlLabel value="GPT4o" control={<Radio />} label="GPT4o" />
            <FormControlLabel value="gemini" control={<Radio />} label="gemini" />
            <FormControlLabel value="claude" control={<Radio />} label="claude" />
          </RadioGroup>
        </FormControl>

        {/**/}
        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333'}}>
          Framework selection
        </Typography>

        <FormControl>
          <RadioGroup
            row
            defaultValue="BioResearcher"
            aria-labelledby="framework"
            onChange={handleFrameworkChange}
            name="row-radio-buttons-group"
          >
            <FormControlLabel value="BioResearcher" control={<Radio />} label="BioResearcher" />
            <FormControlLabel value="ReAct" control={<Radio />} label="ReAct" />
            <FormControlLabel value="Plan-and-Execute" control={<Radio />} label="Plan-and-Execute" />
          </RadioGroup>
        </FormControl>

        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}>
          Other parameters(optional)
        </Typography>
        <Grid container spacing={2}>
          <Grid item="true" size={6}>
            <TextField
              label="Number of references"
              variant="outlined"
              value={refNum}
              onInput={handleInputRefNum}
              fullWidth
            />
          </Grid>
          <Grid item="true" size={6}>
            <TextField
              label="Reviewer maximum round"
              variant="outlined"
              value={reviewerRound}
              onInput={handleInputReviewerRound}
              fullWidth
            />
          </Grid>
        </Grid>

        <Button
          variant="contained"
          color="primary"
          size="large"
          sx={{ mt: 2, mb: 2}}
          onClick={handleSubmit}
        >
          Create
        </Button>
      </Box>
    </Box>
  );
}
