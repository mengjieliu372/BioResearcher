import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import ProgramContent from '../../components/ProgramContent';
import { useParams } from 'react-router-dom';
import { getProgram } from '../../services/api';  // 要换成 getProgram，但后端还没写好 --已改好
import ErrorPage from '../../components/ErrorPage';


function CustomTabPanel(props) {
    const { children, value, index, ...other } = props;
  
    return (
      <div
        role="tabpanel"
        hidden={value !== index}
        id={`simple-tabpanel-${index}`}
        aria-labelledby={`simple-tab-${index}`}
        {...other}
      >
        {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
      </div>
    );
}
  
CustomTabPanel.propTypes = {
children: PropTypes.node,
index: PropTypes.number.isRequired,
value: PropTypes.number.isRequired,
};

function a11yProps(index) {
return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
};
}



export default function Programming() {
    const [value, setValue] = React.useState(0);
    const [content, setContent] = React.useState(null);
    const { id } = useParams();
  
    React.useEffect(() => {
        getProgram(id, value)   // 对应 api.js 里面的那里，后端写完要换过来 --已改好
        .then((res) => {
          setContent(<ProgramContent data={res.data} />);   // 这里是coding下具体的内容，对应 Line 86；这里 ProgramContent 应该对应 RenderContent
        })
        .catch((err) => {
          setContent(<ErrorPage code={err.status} message={err.response.data.detail} />);
        });
    }, [value]);
  
    const handleChange = (event, newValue) => {
      setValue(newValue);
    };

    return (
        <Box sx={{ width: '100%' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={value} onChange={handleChange} aria-label="basic tabs example" centered>
                    <Tab label="coding" sx={{ textTransform: 'none' }} {...a11yProps(0)} />
                </Tabs>
            </Box>

            <Box
                sx={{
                height: '68vh',
                maxHeight: '70vh',
                overflowY: 'auto',
                width: '70vw',
                ml: 'auto',
                mr: 'auto',
                mt: '2vh',
                borderRadius: '8px',
                boxShadow: 3,
                }}
            >

                <CustomTabPanel value={value} index={0}>
                {content}
                </CustomTabPanel>

            </Box>

        </Box>
    );
}