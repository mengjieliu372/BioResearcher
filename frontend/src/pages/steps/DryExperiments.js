import * as React from 'react';
import PropTypes from 'prop-types';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import DryExpContent from '../../components/DryExpContent';
import { useParams } from 'react-router-dom';
import { getCompletedSteps, getDryExp } from '../../services/api';
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

const asErrorMessage = (err) => {
  const detail = err?.response?.data?.detail ?? err?.response?.data?.message ?? err?.message;
  if (typeof detail === 'string') return detail;
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail || 'Unknown error');
  }
};

export default function BasicTabs() {
  const [versions, setVersions] = React.useState([1, 2, 3]);
  const [selectedVersion, setSelectedVersion] = React.useState(1);
  const [content, setContent] = React.useState(null);
  const { id } = useParams();

  React.useEffect(() => {
    getCompletedSteps(id)
      .then((res) => {
        const payload = res.data || {};
        const available = Array.isArray(payload.dry_available_versions)
          ? payload.dry_available_versions.filter((v) => Number.isInteger(v) && v > 0)
          : [];
        const nextVersions = available.length > 0 ? available : [1, 2, 3];
        setVersions(nextVersions);
        if (!nextVersions.includes(selectedVersion)) {
          setSelectedVersion(nextVersions[0]);
        }
      })
      .catch(() => {
        setVersions([1, 2, 3]);
        setSelectedVersion(1);
      });
  }, [id, selectedVersion]);

  React.useEffect(() => {
    getDryExp(id, selectedVersion - 1)
      .then((res) => {
        setContent(<DryExpContent data={res.data} />);
      })
      .catch((err) => {
        setContent(
          <ErrorPage
            code={err.response?.status || err.status || 500}
            message={asErrorMessage(err)}
          />
        );
      });
  }, [id, selectedVersion]);

  const handleChange = (event, newValue) => {
    const nextVersion = versions[newValue];
    if (nextVersion !== undefined) {
      setSelectedVersion(nextVersion);
    }
  };

  const tabValue = Math.max(0, versions.indexOf(selectedVersion));

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        height: '78vh',
        maxHeight: '78vh',
      }}
    >
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleChange} centered>
          {versions.map((version, index) => (
            <Tab
              key={version}
              label={`Dry Experiment ${version}`}
              {...a11yProps(index)}
              sx={{ textTransform: 'none' }}
            />
          ))}
        </Tabs>
      </Box>

      <Box
        sx={{
          height: '72vh',
          maxHeight: '72vh',
          overflowY: 'auto',
          width: '65vw',
          ml: 'auto',
          mr: 'auto',
          borderRadius: '8px',
          boxShadow: 3,
        }}
      >
        <CustomTabPanel value={tabValue} index={tabValue}>
          {content}
        </CustomTabPanel>
      </Box>
    </Box>
  );
}
