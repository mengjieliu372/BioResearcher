import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authLogin } from '../services/api';
import { isLoggedIn, setAuthSession, setWelcomeNotice } from '../utils/auth';
import bg1 from '../assets/login/1.jpg';
import bg2 from '../assets/login/2.jpg';
import bg3 from '../assets/login/3.jpg';
import xmuLogo from '../assets/login/logo.png';
import qcodeIcon from '../assets/login/qcode.png';
import loginQrImage from '../assets/login/getCode.png';
import userIcon from '../assets/login/user1.png';
import passIcon from '../assets/login/pass1.png';
import './LoginPage.css';

const bgs = [bg1, bg2, bg3];

const TEXT = {
  zh: {
    title: '统一身份认证',
    qrTab: '扫码登录',
    accountTab: '账号登录',
    qrTip: '企业微信扫码登录',
    qrExpired: '连接超时，二维码失效',
    usernamePh: '请输入学号/工号',
    passwordPh: '请输入密码',
    login: '登录',
    loading: '处理中...',
    onlineHelp: '在线帮助',
    forgotPassword: '忘记密码',
    notice1: '学生校友账号禁用可通过忘记密码进行重置',
    notice2: '首次登录请点击忘记密码进行重置；更多请点在线帮助',
    security: '严禁在本互联网非涉密平台传输、处理国家秘密，请确认扫描上传、处理的文件资料不涉及国家秘密',
    loginFailed: '账号密码错误',
    zh: '中文',
    en: 'English',
    copyright: 'Copyright © 厦门大学',
  },
  en: {
    title: 'Unified Identity',
    qrTab: 'QR Login',
    accountTab: 'Account Login',
    qrTip: 'Scan with WeCom',
    qrExpired: 'Connection timeout, QR code expired',
    usernamePh: 'Student/Staff ID',
    passwordPh: 'Password',
    login: 'Login',
    loading: 'Loading...',
    onlineHelp: 'Online Help',
    forgotPassword: 'Forgot Password',
    notice1: 'Disabled student/alumni accounts can be reset via Forgot Password.',
    notice2: 'For first login, reset password first; see Online Help for details.',
    security: 'Do not process confidential data on non-secure internet platforms.',
    loginFailed: 'Invalid account or password',
    zh: '中文',
    en: 'English',
    copyright: 'Copyright © Xiamen University',
  },
};

export default function LoginPage() {
  const navigate = useNavigate();
  const [lang, setLang] = React.useState('zh');
  const [tab, setTab] = React.useState('account');
  const [bgIndex, setBgIndex] = React.useState(0);
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [msg, setMsg] = React.useState('');
  const t = TEXT[lang];

  React.useEffect(() => {
    if (isLoggedIn()) {
      navigate('/manage-project', { replace: true });
    }
  }, [navigate]);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setBgIndex((v) => (v + 1) % bgs.length);
    }, 10000);
    return () => clearInterval(timer);
  }, []);

  const onSubmit = async () => {
    const id = username.trim();
    const pwd = password;
    if (!/^\d{10,14}$/.test(id) || !pwd) {
      setMsg(t.loginFailed);
      return;
    }
    setLoading(true);
    setMsg('');
    try {
      const res = await authLogin({ username: id, password: pwd });
      const token = res?.data?.token || '';
      const user = res?.data?.user || { username: id };
      const welcomeMessage = res?.data?.welcome_message || '';
      const isNewUser = Boolean(res?.data?.is_new_user);
      setAuthSession(token, user);
      setWelcomeNotice({ message: welcomeMessage, isNewUser });
      navigate('/manage-project', { replace: true });
    } catch {
      setMsg(t.loginFailed);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="xmu-login-page">
      <div className="xmu-bg-slider">
        {bgs.map((bg, idx) => (
          <img
            key={idx}
            src={bg}
            alt="login background"
            className={`xmu-bg-slide ${idx === bgIndex ? 'active' : ''}`}
          />
        ))}
      </div>

      <div className="xmu-language-box">
        <button className={`xmu-lang-btn ${lang === 'en' ? 'active' : ''}`} onClick={() => setLang('en')}>
          {t.en}
        </button>
        <button className={`xmu-lang-btn ${lang === 'zh' ? 'active' : ''}`} onClick={() => setLang('zh')}>
          {t.zh}
        </button>
      </div>

      <div className="xmu-login-wrap">
        <img src={qcodeIcon} alt="switch mode" className="xmu-corner-icon" />

        <section className="xmu-main">
          <div className="xmu-school-logo">
            <img src={xmuLogo} alt="xmu" />
            <p className="xmu-login-title">{t.title}</p>
          </div>

          <div className="xmu-tab-head">
            <button className={`xmu-tab ${tab === 'qr' ? 'active' : ''}`} onClick={() => setTab('qr')}>
              {t.qrTab}
            </button>
            <button className={`xmu-tab ${tab === 'account' ? 'active' : ''}`} onClick={() => setTab('account')}>
              {t.accountTab}
            </button>
          </div>

          {tab === 'qr' ? (
            <div className="xmu-qr-panel">
              <div className="xmu-qr-box">
                <img src={loginQrImage} alt="login qr code" className="xmu-qr-image" />
              </div>
              <span className="xmu-qr-tip">{t.qrTip}</span>
              <span className="xmu-qr-expired">{t.qrExpired}</span>
            </div>
          ) : (
            <div className="xmu-account-panel">
              <div className="xmu-input-row">
                <span className="xmu-prex-icon"><img src={userIcon} alt="user" /></span>
                <input
                  value={username}
                  onChange={(e) => setUsername(e.target.value.replace(/[^\d]/g, ''))}
                  placeholder={t.usernamePh}
                  className="xmu-input"
                  maxLength={14}
                />
              </div>
              <div className="xmu-input-row">
                <span className="xmu-prex-icon"><img src={passIcon} alt="pass" /></span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t.passwordPh}
                  className="xmu-input"
                  onKeyDown={(e) => e.key === 'Enter' && onSubmit()}
                />
              </div>
              <div className="xmu-btn-row">
                <button className="xmu-login-btn" onClick={onSubmit} disabled={loading}>
                  {loading ? t.loading : t.login}
                </button>
              </div>
              <div className="xmu-help-row">
                <button type="button" className="xmu-link-btn">{t.onlineHelp}</button>
                <button type="button" className="xmu-link-btn">{t.forgotPassword}</button>
              </div>
              <div className="xmu-msg xmu-msg-error">{msg}</div>
              <div className="xmu-notice">{t.notice1}</div>
              <div className="xmu-notice">{t.notice2}</div>
            </div>
          )}
        </section>

        <div className="xmu-login-tip">{t.security}</div>
      </div>

      <div className="xmu-swiper-pagination">
        {bgs.map((_, idx) => (
          <span
            key={idx}
            className={`xmu-dot ${idx === bgIndex ? 'active' : ''}`}
            onClick={() => setBgIndex(idx)}
          />
        ))}
      </div>

      <div className="xmu-copyright">{t.copyright}</div>
    </div>
  );
}
