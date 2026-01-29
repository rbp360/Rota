import React, { useState, useEffect } from 'react';
import { UserPlus, Calendar, ShieldCheck, Settings, MessageSquare, AlertCircle, CheckCircle, RotateCcw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const App = () => {
  const [activeTab, setActiveTab] = useState('absence');
  const [absentPerson, setAbsentPerson] = useState('');
  const [periods, setPeriods] = useState([]);
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const [currentAbsenceId, setCurrentAbsenceId] = useState(null);
  const [coveredPeriods, setCoveredPeriods] = useState([]);
  const [detailedCovers, setDetailedCovers] = useState({}); // {period: staffName}
  const [showSummary, setShowSummary] = useState(false);
  const [showQuickStatus, setShowQuickStatus] = useState(false);
  const [selectedDay, setSelectedDay] = useState('Thursday');
  const [availableStaff, setAvailableStaff] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [dailyRota, setDailyRota] = useState([]);

  const API_URL = "http://127.0.0.1:8000";

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  const getTargetDate = (dayName) => {
    const today = new Date();
    const currentDayNum = today.getDay(); // 0 is Sunday, 1 is Monday...
    const dayIndices = { 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5 };
    const targetIndex = dayIndices[dayName];

    // Calculate difference (assuming we want the date in the current week)
    const diff = targetIndex - currentDayNum;
    const targetDate = new Date(today);
    targetDate.setDate(today.getDate() + diff);
    return targetDate.toISOString().split('T')[0];
  };

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  useEffect(() => {
    const fetchAvailability = async () => {
      if (periods.length === 0) {
        setAvailableStaff([]);
        return;
      }
      try {
        const targetDate = getTargetDate(selectedDay);
        const res = await axios.get(`${API_URL}/availability?periods=${periods.join(',')}&day=${selectedDay}&date=${targetDate}`);
        setAvailableStaff(res.data);
      } catch (err) {
        console.error("Failed to fetch availability:", err);
      }
    };
    fetchAvailability();
  }, [periods, selectedDay]);

  useEffect(() => {
    const fetchStaff = async () => {
      try {
        const res = await axios.get(`${API_URL}/staff`);
        setStaffList(res.data.map(s => s.name));
      } catch (err) {
        console.error("Failed to fetch staff:", err);
      }
    };
    fetchStaff();
  }, []);

  const fetchDailyRota = async () => {
    try {
      const targetDate = getTargetDate(selectedDay);
      const res = await axios.get(`${API_URL}/daily-rota`, {
        params: { date: targetDate }
      });
      setDailyRota(res.data);
    } catch (err) {
      console.error("Failed to fetch daily rota:", err);
    }
  };

  useEffect(() => {
    if (activeTab === 'rota') {
      fetchDailyRota();
    }
  }, [activeTab, selectedDay]);

  const fetchDetailedCovers = async (aid) => {
    if (!aid) return;
    try {
      const res = await axios.get(`${API_URL}/covers/${aid}`);
      const mapping = {};
      res.data.forEach(c => {
        mapping[c.period] = c.staff_name;
      });
      setDetailedCovers(mapping);
      setCoveredPeriods(res.data.map(c => c.period));
    } catch (err) {
      console.error("Failed to fetch covers:", err);
    }
  };

  useEffect(() => {
    if (currentAbsenceId) {
      fetchDetailedCovers(currentAbsenceId);
    } else {
      setDetailedCovers({});
      setCoveredPeriods([]);
    }
  }, [currentAbsenceId]);

  // Helper to ensure an absence record exists in the DB
  const ensureAbsence = async () => {
    if (currentAbsenceId) return currentAbsenceId;

    try {
      const res = await axios.post(`${API_URL}/absences`, null, {
        params: {
          staff_name: absentPerson,
          date: getTargetDate(selectedDay),
          start_period: Math.min(...periods),
          end_period: Math.max(...periods)
        }
      });
      setCurrentAbsenceId(res.data.id);
      return res.data.id;
    } catch (err) {
      console.error("Failed to create absence:", err);
      setToast({ type: 'error', message: 'Failed to initialize absence record.' });
      return null;
    }
  };

  const handleSuggest = async () => {
    if (!absentPerson || periods.length === 0) return;
    setLoading(true);
    try {
      const aid = await ensureAbsence();
      if (!aid) { setLoading(false); return; }

      const suggestRes = await axios.get(`${API_URL}/suggest-cover/${aid}?day=${selectedDay}`);
      setSuggestions(suggestRes.data.suggestions);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      setLoading(false);
    }
  };

  const handleAssignCover = async (staffName) => {
    if (!absentPerson || periods.length === 0) {
      setToast({ type: 'error', message: 'Select absent staff and periods first!' });
      return;
    }

    try {
      const aid = await ensureAbsence();
      if (!aid) return;

      await axios.post(`${API_URL}/assign-cover`, null, {
        params: {
          absence_id: aid,
          staff_name: staffName,
          periods: periods.join(',')
        }
      });

      setCoveredPeriods(prev => [...new Set([...prev, ...periods])]);
      setDetailedCovers(prev => {
        const next = { ...prev };
        periods.forEach(p => next[p] = staffName);
        return next;
      });
      setPeriods([]); // Deselect periods after assignment
      setSuggestions(null); // Clear suggestions
      setToast({ type: 'success', message: `${staffName} assigned to periods ${periods.join(', ')}` });
    } catch (error) {
      console.error("Error assigning cover:", error);
      setToast({ type: 'error', message: 'Failed to assign cover.' });
    }
  };

  const handlePeriodClick = async (p) => {
    // If it's already covered (green), clicking it should UNCOVER it (undo)
    if (coveredPeriods.includes(p)) {
      if (!currentAbsenceId) return;
      try {
        await axios.delete(`${API_URL}/unassign-cover`, {
          params: { absence_id: currentAbsenceId, period: p }
        });
        setCoveredPeriods(prev => prev.filter(x => x !== p));
        setDetailedCovers(prev => {
          const next = { ...prev };
          delete next[p];
          return next;
        });
        setToast({ type: 'info', message: `Unassigned period ${p}` });
      } catch (err) {
        setToast({ type: 'error', message: 'Failed to unassign.' });
      }
      return;
    }

    // Otherwise, normal toggle for the selection (purple)
    setPeriods(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
  };

  const selectAllDay = () => {
    setPeriods([1, 2, 3, 4, 5, 6, 7, 8]);
  };

  return (
    <div className="container">
      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            style={{
              position: 'fixed', bottom: '2rem', left: '50%', transform: 'translateX(-50%)',
              zIndex: 1000, background: toast.type === 'success' ? 'var(--accent)' : (toast.type === 'info' ? 'var(--primary)' : 'var(--danger)'),
              padding: '1rem 2rem', borderRadius: '2rem', boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'white',
              fontWeight: '600'
            }}
          >
            {toast.type === 'success' ? <CheckCircle size={20} /> : (toast.type === 'info' ? <RotateCcw size={20} /> : <AlertCircle size={20} />)}
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      <header style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', color: 'var(--brand-blue)' }}>St Andrews <span style={{ color: 'var(--brand-green)' }}>RotaAI</span></h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: '500' }}>Green Valley | Intelligent Cover Management</p>
        </div>
        <div className="glass" style={{
          padding: '0.4rem',
          display: 'flex',
          gap: '0.4rem',
          position: 'relative',
          zIndex: showQuickStatus ? 4000 : 10
        }}>
          <button
            onClick={() => setShowQuickStatus(!showQuickStatus)}
            className={showQuickStatus ? 'btn-nav' : 'glass'}
            style={{ padding: '0.4rem 0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            title="Toggle Coverage Overview"
          >
            <ShieldCheck size={16} color={showQuickStatus ? 'white' : 'var(--primary)'} />
            <span style={{ fontSize: '0.8rem' }}>Status</span>
          </button>

          <AnimatePresence>
            {showQuickStatus && (
              <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                className="glass"
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  width: '320px',
                  padding: '1.5rem',
                  marginTop: '0.75rem',
                  zIndex: 3000,
                  boxShadow: '0 20px 50px rgba(0,0,0,0.1)',
                  border: '1px solid var(--primary)',
                  color: 'var(--text-main)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h4 style={{ margin: 0, fontSize: '1rem' }}>Coverage Status</h4>
                  <button onClick={() => setShowQuickStatus(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
                </div>

                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  {absentPerson ? `Absence: ${absentPerson}` : 'No staff selected'}
                </p>

                {/* Visual Strip */}
                <div style={{ display: 'flex', gap: '4px', marginBottom: '1.5rem' }}>
                  {[1, 2, 3, 4, 5, 6, 7, 8].map(p => (
                    <div key={p} style={{
                      flex: 1,
                      height: '10px',
                      background: coveredPeriods.includes(p) ? 'var(--accent)' : 'var(--danger)',
                      borderRadius: '2px',
                      opacity: coveredPeriods.includes(p) ? 1 : 0.6
                    }} title={`Period ${p}: ${detailedCovers[p] || 'Uncovered'}`} />
                  ))}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', maxHeight: '300px', overflowY: 'auto', paddingRight: '4px' }}>
                  {(() => {
                    const allPeriods = [1, 2, 3, 4, 5, 6, 7, 8];
                    let currentStaff = detailedCovers[1] || null;
                    let start = 1;
                    let summaryParts = [];

                    for (let p = 2; p <= 9; p++) {
                      const staff = detailedCovers[p] || null;
                      if (staff !== currentStaff || p === 9) {
                        const range = start === p - 1 ? `P${start}` : `P${start}-${p - 1}`;
                        summaryParts.push({ range, staff: currentStaff });
                        start = p;
                        currentStaff = staff;
                      }
                    }

                    return summaryParts.map((part, i) => (
                      <div key={i} style={{
                        fontSize: '0.8rem',
                        padding: '0.65rem',
                        borderRadius: '0.5rem',
                        background: !part.staff ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                        color: !part.staff ? 'var(--danger)' : 'var(--accent)',
                        borderLeft: `4px solid ${!part.staff ? 'var(--danger)' : 'var(--accent)'}`,
                        display: 'flex',
                        justifyContent: 'space-between'
                      }}>
                        <span style={{ fontWeight: 600 }}>{part.range}</span>
                        <span>{part.staff ? part.staff : 'HOLE'}</span>
                      </div>
                    ));
                  })()}
                </div>

                {!absentPerson && (
                  <div style={{ fontSize: '0.75rem', textAlign: 'center', marginTop: '1rem', color: 'var(--text-muted)' }}>
                    Select a staff member to see their cover situation.
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          <button onClick={() => setActiveTab('absence')} className={activeTab === 'absence' ? 'btn-nav' : ''} style={{ padding: '0.4rem 0.8rem', fontSize: '0.875rem' }}>Absence</button>
          <button onClick={() => setActiveTab('rota')} className={activeTab === 'rota' ? 'btn-nav' : ''} style={{ padding: '0.4rem 0.8rem', fontSize: '0.875rem' }}>Daily Rota</button>
          <button onClick={() => setActiveTab('settings')} className={activeTab === 'settings' ? 'btn-nav' : ''} style={{ padding: '0.4rem 0.8rem', fontSize: '0.875rem' }}><Settings size={16} /></button>
        </div>
      </header>

      <div className="glass" style={{ padding: '0.5rem', marginBottom: '1rem', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
        {days.map(d => (
          <button
            key={d}
            onClick={() => { setSelectedDay(d); setCoveredPeriods([]); setDetailedCovers({}); setCurrentAbsenceId(null); setSuggestions(null); }}
            className={selectedDay === d ? 'btn-nav' : 'glass'}
            style={{ padding: '0.4rem 1rem', flex: 1, minWidth: '80px', fontSize: '0.875rem' }}
          >
            {d}
          </button>
        ))}
      </div>

      <main>
        {activeTab === 'absence' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 350px) 1fr', gap: '1rem', alignItems: 'start' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="glass" style={{ padding: '1.25rem' }}>
                <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <UserPlus size={18} color="var(--primary)" /> Who is Absent?
                </h3>
                <div style={{ marginBottom: '0.75rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Select Staff</label>
                  <select style={{ padding: '0.5rem', fontSize: '0.875rem' }} value={absentPerson} onChange={(e) => { setAbsentPerson(e.target.value); setCoveredPeriods([]); setDetailedCovers({}); setCurrentAbsenceId(null); setSuggestions(null); }}>
                    <option value="">Select a person...</option>
                    {staffList.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Periods Absent</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', marginBottom: '0.75rem' }}>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(p => {
                      const isCovered = coveredPeriods.includes(p);
                      const isSelected = periods.includes(p);
                      return (
                        <button
                          key={p}
                          onClick={() => handlePeriodClick(p)}
                          className="glass"
                          style={{
                            padding: '0.4rem',
                            fontSize: '0.8rem',
                            background: isCovered ? 'var(--accent)' : (isSelected ? 'var(--primary)' : 'transparent'),
                            borderColor: isCovered ? 'var(--accent)' : (isSelected ? 'var(--primary)' : 'var(--border)'),
                            color: (isCovered || isSelected) ? 'white' : 'var(--text-main)',
                            transition: 'all 0.3s ease'
                          }}
                        >
                          {isCovered ? <CheckCircle size={12} style={{ marginRight: '2px' }} /> : ''} P{p}
                        </button>
                      );
                    })}
                  </div>
                  <button
                    onClick={selectAllDay}
                    className="glass"
                    style={{ width: '100%', padding: '0.4rem', fontSize: '0.8rem', background: periods.length === 8 ? 'var(--primary)' : 'rgba(0,0,0,0.03)', color: periods.length === 8 ? 'white' : 'var(--text-main)' }}
                  >
                    Select All Day
                  </button>
                </div>

                <button
                  className="btn-primary"
                  style={{ width: '100%', marginBottom: '0.75rem', padding: '0.6rem' }}
                  onClick={handleSuggest}
                  disabled={!absentPerson || periods.length === 0}
                >
                  {loading ? 'Analyzing...' : 'Generate AI Suggestions'}
                </button>

                <button
                  className="glass"
                  style={{ width: '100%', padding: '0.6rem', fontSize: '0.875rem', borderColor: 'var(--primary)', color: 'var(--primary)' }}
                  onClick={() => setShowSummary(true)}
                  disabled={!absentPerson}
                >
                  View Cover Summary
                </button>
              </div>

              <div className="glass" style={{ padding: '1.25rem', minHeight: '200px' }}>
                <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={18} color="var(--accent)" /> AI Suggestion
                </h3>

                <AnimatePresence>
                  {!suggestions && !loading && (
                    <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)' }}>
                      <AlertCircle size={32} style={{ marginBottom: '0.5rem', opacity: 0.5 }} />
                      <p style={{ fontSize: '0.75rem' }}>Generate AI suggestions or pick below.</p>
                    </div>
                  )}

                  {loading && (
                    <div style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0' }}>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        style={{ width: '30px', height: '30px', border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%' }}
                      />
                    </div>
                  )}

                  {suggestions && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <div className="glass" style={{ padding: '0.75rem', marginBottom: '0.75rem', background: 'rgba(43, 83, 196, 0.03)', whiteSpace: 'pre-line', fontSize: '0.75rem', lineHeight: '1.4' }}>
                        {suggestions}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <div className="glass" style={{ padding: '1.5rem', height: '100%' }}>
              <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem' }}>
                <Calendar size={22} color="var(--primary)" /> Availability Checker
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
                  {periods.length > 0 ? `(Target: P${periods.sort().join(', P')})` : '(Select periods)'}
                </span>
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
                {availableStaff.filter(s => s.name !== absentPerson).length > 0 ? (
                  availableStaff.filter(s => s.name !== absentPerson).map((s, i) => {
                    const isBusySpecialist = !s.is_free;
                    let bgColor = 'white';
                    let borderColor = 'var(--border)';

                    if (s.is_priority && s.is_free) {
                      bgColor = 'rgba(43, 83, 196, 0.08)';
                      borderColor = 'var(--primary)';
                    } else if (isBusySpecialist) {
                      bgColor = 'rgba(239, 68, 68, 0.15)';
                      borderColor = '#ef4444';
                    }

                    return (
                      <motion.div
                        key={i}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleAssignCover(s.name)}
                        className="glass"
                        style={{
                          padding: '0.6rem',
                          cursor: 'pointer',
                          background: bgColor,
                          border: `1px solid ${borderColor}`,
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                          <div style={{ fontWeight: '700', fontSize: '0.9rem', color: s.is_priority && s.is_free ? 'var(--primary)' : (isBusySpecialist ? '#ef4444' : 'var(--text-main)') }}>
                            {s.name}
                          </div>
                          {!s.is_free && <span style={{ fontSize: '0.6rem', background: '#ef4444', padding: '1px 4px', borderRadius: '3px', color: 'white' }}>BUSY</span>}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{s.profile || 'Staff Member'}</div>
                        {s.activity && s.activity !== 'Free' && (
                          <div style={{
                            fontSize: '0.7rem',
                            padding: '2px 4px',
                            borderRadius: '4px',
                            background: s.is_free ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            color: s.is_free ? 'var(--accent)' : '#ef4444',
                            fontWeight: '600'
                          }}>
                            {s.is_free ? s.activity : `Doing: ${s.activity}`}
                          </div>
                        )}
                      </motion.div>
                    );
                  })
                ) : (
                  <p style={{ color: 'var(--text-muted)', gridColumn: '1/-1', fontSize: '0.875rem' }}>
                    {periods.length > 0 ? 'No staff members are free for all selected periods.' : 'Select periods to see availability.'}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'rota' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--primary)' }}>
                <Calendar size={28} /> Daily Cover Sheet: {selectedDay}
              </h2>
              <button className="btn-primary" onClick={fetchDailyRota} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <RotateCcw size={18} /> Refresh
              </button>
            </div>

            {dailyRota.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                <ShieldCheck size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                <p>No absences logged for today yet.</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '1.5rem' }}>
                {dailyRota.map((row, idx) => {
                  const requiredCovers = row.end_period - row.start_period + 1;
                  const isFullyCovered = row.covers.length >= requiredCovers;

                  return (
                    <div key={idx} className="glass" style={{ padding: '1.5rem', borderLeft: `6px solid ${isFullyCovered ? 'var(--accent)' : 'var(--danger)'}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                        <div>
                          <h3 style={{ margin: 0, fontSize: '1.25rem' }}>{row.staff_name}</h3>
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Absent: Periods {row.start_period}-{row.end_period}</p>
                        </div>
                        <span style={{
                          background: isFullyCovered ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                          color: isFullyCovered ? 'var(--accent)' : 'var(--danger)',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '1rem',
                          fontSize: '0.75rem',
                          fontWeight: '700',
                          border: '1px solid currentColor'
                        }}>
                          {isFullyCovered ? 'FULLY COVERED' : 'PARTIAL COVER'}
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.75rem' }}>
                        {Array.from({ length: requiredCovers }, (_, i) => row.start_period + i).map(p => {
                          const coverage = row.covers.find(c => c.period === p);
                          return (
                            <div key={p} className="glass" style={{
                              padding: '0.75rem',
                              textAlign: 'center',
                              background: coverage ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)',
                              borderColor: coverage ? 'var(--accent)' : 'var(--danger)',
                              position: 'relative'
                            }}>
                              <div style={{ fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>P{p}</div>
                              <div style={{ fontSize: '0.85rem', color: coverage ? 'var(--accent)' : 'var(--danger)', marginBottom: coverage ? '0.5rem' : '0' }}>
                                {coverage ? coverage.covering_staff_name : '🚨 NEEDS COVER'}
                              </div>
                              {coverage && (
                                <button
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    try {
                                      await axios.delete(`${API_URL}/unassign-cover`, {
                                        params: { absence_id: row.absence_id, period: p }
                                      });
                                      fetchDailyRota(); // Refresh list
                                      setToast({ type: 'info', message: `Unassigned ${coverage.covering_staff_name} from Period ${p}` });
                                    } catch (err) {
                                      setToast({ type: 'error', message: 'Failed to unassign.' });
                                    }
                                  }}
                                  style={{
                                    background: 'var(--danger)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    padding: '2px 8px',
                                    fontSize: '0.65rem',
                                    cursor: 'pointer',
                                    fontWeight: 'bold'
                                  }}
                                >
                                  UNASSIGN
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}
      </main>

      {/* Cover Summary Modal */}
      <AnimatePresence>
        {showSummary && (
          <div className="modal-overlay" onClick={() => setShowSummary(false)} style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(30, 41, 59, 0.4)', backdropFilter: 'blur(4px)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem'
          }}>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass"
              style={{ width: '100%', maxWidth: '500px', padding: '2rem' }}
            >
              <h2 style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--primary)' }}>
                Cover Summary: {absentPerson}
                <button onClick={() => setShowSummary(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.5rem' }}>×</button>
              </h2>
              <div style={{ display: 'grid', gap: '1rem' }}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map(p => (
                  <div key={p} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '1rem', borderRadius: '1rem',
                    background: coveredPeriods.includes(p) ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    border: `1px solid ${coveredPeriods.includes(p) ? '#22c55e' : '#ef4444'}`
                  }}>
                    <span style={{ fontWeight: 'bold' }}>Period {p}</span>
                    <span style={{ color: coveredPeriods.includes(p) ? '#22c55e' : '#ef4444', fontWeight: '500' }}>
                      {detailedCovers[p] ? `Covered by: ${detailedCovers[p]}` : 'UNCOVERED'}
                    </span>
                  </div>
                ))}
              </div>
              <button className="btn-primary" style={{ width: '100%', marginTop: '2rem' }} onClick={() => setShowSummary(false)}>Close</button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <div style={{ position: 'fixed', bottom: '2rem', right: '2rem' }}>
        <button className="btn-primary" style={{ borderRadius: '50%', width: '3.5rem', height: '3.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <MessageSquare />
        </button>
      </div>
    </div>
  );
};

export default App;
