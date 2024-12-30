import * as React from 'react';
import Table from '@mui/material/Table';
import Typography from '@mui/material/Typography';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Container from '@mui/material/Container';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TablePagination from '@mui/material/TablePagination';
import TableFooter from '@mui/material/TableFooter';
import Grid from '@mui/material/Grid2';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControl from '@mui/material/FormControl';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import IconButton from '@mui/material/IconButton';
import DeleteIcon from '@mui/icons-material/Delete';
import Box from '@mui/material/Box';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getProjects, updateProject, deleteProject } from '../services/api';
import { uploadFile, deleteFile } from '../services/api';

function createData(id, name) {
  return { id, name };
}

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

export default function BasicTable() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [projects, setProjects] = useState([]);
  const [files, setFiles] = useState([]);
  const [expInfo, setExpInfo] = useState({
    expName: '',
    expPurpose: '',
    expCondition: '',
    expRequirement: '',
    paperset: { PMC: false, PubMed: false },
    dataset: { GEO: false, NCBI: false, cBioPortal: false },
    llmModel: '',
    refNum: 0,
    reviewerRound: 0,
    fileNames: []
  });

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await getProjects();
        setProjects(response.data);
      }
      catch (error) {
        console.log('Failed to fetch projects:', error);
      }
    };
    fetchProjects();
  }, []);

  const rows = projects.map((project) => createData(project.id, project.expName));

  const handleOpen = (id) => {
    navigate(`/${id}/steps`);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleEdit = (id) => {
    const project = projects.find((p) => p.id === id);
    setExpInfo(project);
    setFiles(project.fileNames.map((name) => ({ name, status: 'Uploaded' })));
    setOpen(true);
  };

  const handleDelete = (id) => {
    // 提示用户是否删除
    if (!window.confirm('Are you sure you want to delete this project?')) {
      return;
    }

    deleteProject(id).then(() => {
      const newProjects = projects.filter((project) => project.id !== id);
      setProjects(newProjects);
    });
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage); // 更新当前页
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10)); // 更新每页显示条数
    setPage(0); // 重置回第一页
  };

  const handlePaperChange = (event) => {
    setExpInfo({
      ...expInfo,
      paperset: {
        ...expInfo.paperset,
        [event.target.name]: event.target.checked
      }
    });
  };

  const handleDatabaseChange = (event) => {
    setExpInfo({
      ...expInfo,
      dataset: {
        ...expInfo.dataset,
        [event.target.name]: event.target.checked
      }
    });
  };

  const handleLlmModelChange = (event) => {
    setExpInfo({ ...expInfo, llmModel: event.target.value });
  };

  const handleInputRefNum = (event) => {
    setExpInfo({ ...expInfo, refNum: event.target.value });
  };

  const handleInputReviewerRound = (event) => {
    setExpInfo({ ...expInfo, reviewerRound: event.target.value });
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
      setFiles([...files, ...newFiles]);
    };
  };

  useEffect(() => {
    const uploadingFiles = files.filter(file => file.status === 'Uploading');
    if (uploadingFiles.length > 0) {
      uploadingFiles.forEach((fileObj, index) => {
        if (fileObj.status === 'Uploaded' || fileObj.status === 'Failed' )
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

  const handleSave = async () => {
    // 数据验证
    if (!expInfo.expName || !expInfo.expPurpose || !expInfo.expCondition || !expInfo.expRequirement) {
      alert('请填写实验相关信息！');
      return;
    }
  
    // 检查paperset和dataset是否全为false
    if (!Object.values(expInfo.paperset).some(Boolean)) {
      alert('请选择要检索的文献库！');
      return;
    }
    if (!Object.values(expInfo.dataset).some(Boolean)) {
      alert('请选择要检索的数据集库！');
      return;
    }
  
    // 检查文件是否上传完成
    if (files.some(file => file.status !== 'Uploaded')) {
      alert('文件上传中，请稍后提交！');
      return;
    }
  
    const fileNames = files.map(file => file.name);
    const updatedExpInfo = { ...expInfo, fileNames };
  
    setExpInfo(updatedExpInfo);
  
    // 更新项目并同步后端数据
    try {
      await updateProject(updatedExpInfo);
      setOpen(false);
  
      const response = await getProjects();
      setProjects(response.data);
      setOpen(false);
    } catch (error) {
      console.log('Failed to update project:', error);
    }
  };
  
  

  const currentRows = rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const emptyRows = page >= 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  return (
    <Container
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'flex-start',
        textAlign: 'center',
        width: '100%',
        height: '90vh',
      }}
    >
      <TableContainer
        component={Paper}
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '8px',
          boxShadow: 3,
          height: '49vh',
        }}
      >
        <Table sx={{ minWidth: 650 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell align="center">ID</TableCell>
              <TableCell align="center">Experiment Name</TableCell>
              <TableCell align="center">Operations</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentRows.map((row) => (
              <TableRow
                key={row.id}
                sx={{
                  '&:last-child td, &:last-child th': { border: 0 },
                  height: '7vh',
                }}
              >
                <TableCell component="th" scope="row" align="center">{row.id}</TableCell>
                <TableCell align="center">{row.name}</TableCell>
                <TableCell align="center">
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={() => handleOpen(row.id)}
                    sx={{ marginRight: 1, textTransform: 'none' }}
                  >
                    Open
                  </Button>
                  <Button
                    variant="outlined"
                    color="secondary"
                    onClick={() => handleEdit(row.id)}
                    sx={{ marginRight: 1, textTransform: 'none' }}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => handleDelete(row.id)}
                    sx={{ textTransform: 'none' }}
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {emptyRows > 0 && (
              <TableRow style={{ height: `${7 * emptyRows}vh` }}>
                <TableCell colSpan={3} />
              </TableRow>
            )}
          </TableBody>

          <TableFooter>
            <TableRow>
              <TablePagination
                rowsPerPageOptions={[5]}
                component="td"
                count={rows.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
              />
            </TableRow>
          </TableFooter>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="md">
        <DialogTitle>Edit the Project</DialogTitle>
        <DialogContent>
          <DialogContentText
            sx={{
              mb: 2,
            }}>
            Modify the experiment details:
          </DialogContentText>

          <Grid container spacing={2}>
            <Grid item="true" size={12}>
              <TextField
                label="Experiment Name"
                variant="outlined"
                required
                fullWidth
                sx={{ mb: 2 }}
                value={expInfo.expName}
                onChange={(e) => setExpInfo({ ...expInfo, expName: e.target.value })}
              />
            </Grid>

            <Grid item="true" size={12}>
              <TextField
                label="Experiment Purpose"
                variant="outlined"
                required
                fullWidth
                sx={{ mb: 2 }}
                value={expInfo.expPurpose}
                onChange={(e) => setExpInfo({ ...expInfo, expPurpose: e.target.value })}
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
                value={expInfo.expCondition}
                onChange={(e) => setExpInfo({ ...expInfo, expCondition: e.target.value })}
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
                value={expInfo.expRequirement}
                onChange={(e) => setExpInfo({ ...expInfo, expRequirement: e.target.value })}
              />
            </Grid>
          </Grid>
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mt: 2 }}>
            选择要检索的数据库
          </Typography>
          <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
            文献库：
          </Typography>

          <FormGroup row sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Checkbox checked={expInfo.paperset.PMC} onChange={handlePaperChange} name='PMC' />}
              label="PMC" />
            <FormControlLabel
              control={<Checkbox checked={expInfo.paperset.PubMed} onChange={handlePaperChange} name='PubMed' />}
              label="PubMed" />
          </FormGroup>
          <Typography variant="h6" sx={{ color: '#555', mb: 1 }}>
            数据集库：
          </Typography>
          <FormGroup row sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Checkbox checked={expInfo.dataset.GEO} onChange={handleDatabaseChange} name='GEO' />}
              label="GEO" />
            <FormControlLabel
              control={<Checkbox checked={expInfo.dataset.NCBI} onChange={handleDatabaseChange} name='NCBI' />}
              label="NCBI" />
            <FormControlLabel
              control={<Checkbox checked={expInfo.dataset.cBioPortal} onChange={handleDatabaseChange} name='cBioPortal' />}
              label="cBioPortal" />
          </FormGroup>

          <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333' }}>
            本地文献上传
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
            <Box sx={{ mb: 2 }}>
              <Typography variant="h6" sx={{ color: '#555', mb: 0.5 }}>
                已选择的文件：
              </Typography>
              <List>
                {files.map((file, index) => (
                  <ListItem key={index} sx={{ display: 'flex', alignItems: 'center', p: 1, borderRadius: 1, bgcolor: 'background.default', mb: 1 }}>
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

          <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}>
            LLM模型选择
          </Typography>

          <FormControl>
            <RadioGroup
              row
              defaultValue="GPT4o"
              aria-labelledby="llm"
              onChange={handleLlmModelChange}
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
            <Grid item="true" size={6}>
              <TextField
                label="参考文献的数量"
                variant="outlined"
                value={expInfo.refNum}
                onInput={handleInputRefNum}
                fullWidth
              />
            </Grid>
            <Grid item="true" size={6}>
              <TextField
                label="Reviewer最大轮次"
                variant="outlined"
                value={expInfo.reviewerRound}
                onInput={handleInputReviewerRound}
                fullWidth
              />
            </Grid>
          </Grid>

        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
