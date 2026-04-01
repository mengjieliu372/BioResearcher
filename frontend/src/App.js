import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AppAppBar from './components/StyledAppBar';

import HomePage from './pages/HomePage';
import NewProject from './pages/NewProject';
import ManageProject from './pages/ManageProject';
import LoginPage from './pages/LoginPage';
import Steps from './components/Steps';
import Search from './pages/steps/Search';
import LiteratureProcessing from './pages/steps/LiteratureProcessing';
import ExperimentalDesign from './pages/steps/ExperimentalDesign';
import DryExperiments from './pages/steps/DryExperiments';
import Programming from './pages/steps/Programming';
import Test from './pages/Test';
import { isLoggedIn } from './utils/auth';

function RequireAuth({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  const location = useLocation();
  const hideAppBar = location.pathname === '/login';

  return (
    <div className="App">
      {!hideAppBar ? <AppAppBar /> : null}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Navigate to={isLoggedIn() ? '/manage-project' : '/login'} replace />} />
        <Route path="/home" element={<RequireAuth><HomePage /></RequireAuth>} />
        <Route path="/new-project" element={<RequireAuth><NewProject /></RequireAuth>} />
        <Route path="/manage-project" element={<RequireAuth><ManageProject /></RequireAuth>} />
        <Route path=":id/steps" element={<RequireAuth><Steps /></RequireAuth>}>
          <Route index element={<Navigate to="search" />} />
          <Route path="search" element={<Search />} />
          <Route path="literature-processing" element={<LiteratureProcessing />} />
          <Route path="experimental-design" element={<ExperimentalDesign />} />
          <Route path="dry-experiments" element={<DryExperiments />} />
          <Route path="programming" element={<Programming />} />
        </Route>
        <Route path="/test" element={<RequireAuth><Test /></RequireAuth>} />
      </Routes>
    </div>
  );
}

export default App;
