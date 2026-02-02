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
  const [showChat, setShowChat] = useState(false);
  const [chatQuery, setChatQuery] = useState('');
  const [chatReport, setChatReport] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [absentSchedule, setAbsentSchedule] = useState([]);
  const [weekOffset, setWeekOffset] = useState(0);

  useEffect(() => {
    const today = new Date();
    const day = today.getDay();
    if (day === 0 || day === 6) {
      setWeekOffset(1);
    }
  }, []);


  const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? "http://127.0.0.1:8000"
    : "https://rota-47dp.onrender.com/api";

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  const getWeekMondayDate = (offset) => {
    const today = new Date();
    const currentDay = today.getDay();
    const diff = today.getDate() - currentDay + (currentDay === 0 ? -6 : 1);
    const monday = new Date(today);
    monday.setDate(diff);
    monday.setDate(monday.getDate() + (offset * 7));
    return monday;
  };

  const getTargetDate = (dayName) => {
    const monday = getWeekMondayDate(weekOffset);
    const dayIndices = { 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4 };
    const add = dayIndices[dayName] !== undefined ? dayIndices[dayName] : 0;
    const target = new Date(monday);
    target.setDate(monday.getDate() + add);
    return target.toISOString().split('T')[0];
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
        const ignore = ["TBC", "External", "Coach", "Room", "Music Room", "Hall", "Gym", "Pitch", "Court", "Pool", "Library", "PRE NURSERY", "PRE NUSERY", "Outside Prov.", "**", "gate", "locked", "at", "8.30", "Mr", "1", "Calire", "?", "Duty"];
        const cleanList = res.data.map(s => s.name).filter(n => !ignore.some(i => n.toLowerCase().includes(i.toLowerCase())));
        setStaffList(cleanList.sort());
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

  useEffect(() => {
    const fetchAbsentSchedule = async () => {
      if (!absentPerson) {
        setAbsentSchedule([]);
        return;
      }
      try {
        const res = await axios.get(`${API_URL}/staff-schedule/${absentPerson}`, {
          params: { day: selectedDay }
        });
        setAbsentSchedule(res.data);
      } catch (err) {
        console.error("Failed to fetch absent schedule:", err);
      }
    };
    fetchAbsentSchedule();
  }, [absentPerson, selectedDay]);

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
    const needCover = absentSchedule.length > 0
      ? absentSchedule.filter(s => !s.is_free).map(s => s.period)
      : [1, 2, 3, 4, 5, 6, 7, 8];
    setPeriods(needCover);
  };

  const handleGenerateReport = async () => {
    if (!chatQuery.trim()) return;
    setChatLoading(true);
    setChatReport(null);
    try {
      const res = await axios.get(`${API_URL}/generate-report`, {
        params: { query: chatQuery }
      });
      setChatReport(res.data.report);
    } catch (err) {
      console.error("Failed to generate report:", err);
      setToast({ type: 'error', message: 'Failed to generate report.' });
    } finally {
      setChatLoading(false);
    }
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
                <div style={{ display: 'flex', gap: '3px', marginBottom: '1rem' }}>
                  {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13].map(p => {
                    const sch = absentSchedule.find(s => s.period === p);
                    if ((p < 1 || p > 8) && (!sch || sch.is_free)) return null;

                    return (
                      <div key={p} style={{
                        flex: 1,
                        height: '10px',
                        background: coveredPeriods.includes(p) ? 'var(--accent)' : 'var(--danger)',
                        borderRadius: '2px',
                        opacity: coveredPeriods.includes(p) ? 1 : 0.6
                      }} title={`${p === 0 ? 'Morn' : (p === 9 ? 'Lunch' : (p === 10 ? 'Aft' : (p === 11 ? 'Break' : (p === 13 ? 'CCA' : `Period ${p}`))))}: ${detailedCovers[p] || 'Uncovered'}`} />
                    );
                  })}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', maxHeight: '300px', overflowY: 'auto', paddingRight: '4px' }}>
                  {(() => {
                    const activePeriods = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13].filter(p => {
                      const sch = absentSchedule.find(s => s.period === p);
                      return (p >= 1 && p <= 8) || (sch && !sch.is_free);
                    }).sort((a, b) => a - b);

                    if (activePeriods.length === 0) return null;

                    let summaryParts = [];
                    let currentStaff = detailedCovers[activePeriods[0]] || null;
                    let rangeStartIdx = 0;

                    for (let i = 1; i <= activePeriods.length; i++) {
                      const p = activePeriods[i];
                      const staff = detailedCovers[p] || null;

                      // Split if staff changes OR if there is a gap in periods OR end of list
                      const isEnd = i === activePeriods.length;
                      const isGap = !isEnd && (activePeriods[i] !== activePeriods[i - 1] + 1);
                      const isStaffChange = !isEnd && staff !== currentStaff;

                      if (isEnd || isGap || isStaffChange) {
                        const startP = activePeriods[rangeStartIdx];
                        const endP = activePeriods[i - 1];

                        const formatP = (num) => {
                          if (num === 0) return "Morn";
                          if (num === 9) return "Lunch";
                          if (num === 10) return "Aft";
                          if (num === 11) return "Break";
                          if (num === 13) return "CCA";
                          return `P${num}`;
                        };

                        const range = startP === endP ? formatP(startP) : `${formatP(startP)}-${formatP(endP)}`;
                        summaryParts.push({ range, staff: currentStaff });

                        if (!isEnd) {
                          rangeStartIdx = i;
                          currentStaff = staff;
                        }
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

      <div className="glass" style={{ padding: '0.8rem', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 0.5rem' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={16} />
            Week Starting: {(() => {
              const m = getWeekMondayDate(weekOffset);
              return `${m.getDate()}/${m.getMonth() + 1}`;
            })()}
            {weekOffset === 0 ? " (Current)" : (weekOffset === 1 ? " (Next Week)" : ` (+${weekOffset} Weeks)`)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>View Advance:</span>
            <input
              type="range"
              min="0"
              max="8"
              value={weekOffset}
              onChange={(e) => {
                setWeekOffset(Number(e.target.value));
                // Reset selections when changing week to avoid confusion
                setCoveredPeriods([]);
                setDetailedCovers({});
                setCurrentAbsenceId(null);
                setSuggestions(null);
              }}
              style={{ cursor: 'pointer', accentColor: 'var(--primary)' }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
          {days.map(d => {
            const dateStr = getTargetDate(d);
            const dateObj = new Date(dateStr);
            const label = `${d} ${dateObj.getDate()}/${dateObj.getMonth() + 1}`;

            return (
              <button
                key={d}
                onClick={() => { setSelectedDay(d); setCoveredPeriods([]); setDetailedCovers({}); setCurrentAbsenceId(null); setSuggestions(null); }}
                className={selectedDay === d ? 'btn-nav' : 'glass'}
                style={{ padding: '0.4rem 1rem', flex: 1, minWidth: '80px', fontSize: '0.85rem' }}
              >
                {label}
              </button>
            );
          })}
        </div>
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
                    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13].map(p => {
                      const isCovered = coveredPeriods.includes(p);
                      const isSelected = periods.includes(p);
                      const scheduleItem = absentSchedule.find(s => s.period === p);
                      const isOriginallyFree = scheduleItem && scheduleItem.is_free;

                      let label = `P${p}`;
                      if (p === 0) label = "Morn";
                      if (p === 9) label = "Lunch";
                      if (p === 10) label = "AftSch";
                      if (p === 11) label = "Break";
                      if (p === 13) label = "CCA";

                      // If absent person has a specific duty here, show it in title
                      const title = scheduleItem && !scheduleItem.is_free ? scheduleItem.activity : `Period ${p}`;

                      // Only show button if: 
                      // 1. It is a teaching period (1-8)
                      // 2. OR it is a non-teaching period AND the user has a duty/CCA there
                      if ((p < 1 || p > 8) && (!scheduleItem || scheduleItem.is_free)) {
                        // Skip irrelevant duty slots if they are free
                        return null;
                      }

                      return (
                        <button
                          key={p}
                          onClick={() => (!isOriginallyFree || p > 8) && handlePeriodClick(p)} // Allow clicking duties even if technically "free" in schedule? No, rely on schedule.
                          className="glass"
                          disabled={isOriginallyFree && p <= 8}
                          title={title}
                          style={{
                            padding: '0.4rem',
                            fontSize: '0.7rem',
                            background: isOriginallyFree && p <= 8 ? 'rgba(0,0,0,0.05)' : (isCovered ? 'var(--accent)' : (isSelected ? 'var(--primary)' : 'transparent')),
                            borderWidth: '1px',
                            borderStyle: (p === 0 || p > 8) ? 'dashed' : 'solid',
                            borderColor: isOriginallyFree && p <= 8 ? 'transparent' : (isCovered ? 'var(--accent)' : (isSelected ? 'var(--primary)' : 'var(--border)')),
                            color: isOriginallyFree && p <= 8 ? 'var(--text-muted)' : ((isCovered || isSelected) ? 'white' : 'var(--text-main)'),
                            cursor: isOriginallyFree && p <= 8 ? 'not-allowed' : 'pointer',
                            opacity: isOriginallyFree && p <= 8 ? 0.6 : 1,
                            textDecoration: isOriginallyFree && p <= 8 ? 'line-through' : 'none',
                            transition: 'all 0.3s ease',
                          }}
                        >
                          {isCovered ? <CheckCircle size={12} style={{ marginRight: '2px' }} /> : ''}
                          {label}
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
                        style={{
                          width: '30px',
                          height: '30px',
                          borderWidth: '3px',
                          borderStyle: 'solid',
                          borderColor: 'var(--border)',
                          borderTopColor: 'var(--primary)',
                          borderRadius: '50%'
                        }}
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

      <div style={{ position: 'fixed', bottom: '2rem', left: '2rem', zIndex: 1000 }}>
        <button
          onClick={() => setShowChat(!showChat)}
          className="btn-primary"
          style={{ borderRadius: '50%', width: '3.5rem', height: '3.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 25px rgba(0,0,0,0.2)' }}
        >
          <MessageSquare />
        </button>
      </div>

      {/* AI Report Chat Modal */}
      <AnimatePresence>
        {showChat && (
          <div className="modal-overlay" onClick={() => setShowChat(false)} style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(30, 41, 59, 0.4)', backdropFilter: 'blur(4px)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem'
          }}>
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="glass"
              style={{ width: '100%', maxWidth: '600px', padding: '2rem', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}
            >
              <h2 style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--brand-blue)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><MessageSquare color="var(--primary)" /> AI Report Generator</span>
                <button onClick={() => setShowChat(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.5rem' }}>×</button>
              </h2>

              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                  Ask anything about the rota history and coverage. For example: "How many times has Ben covered this year?"
                </p>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="text"
                    value={chatQuery}
                    onChange={(e) => setChatQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleGenerateReport()}
                    placeholder="Ask a question..."
                    style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '0.75rem', border: '1px solid var(--border)', fontSize: '1rem' }}
                  />
                  <button
                    onClick={handleGenerateReport}
                    className="btn-primary"
                    disabled={chatLoading || !chatQuery.trim()}
                    style={{ padding: '0.75rem 1.5rem' }}
                  >
                    {chatLoading ? 'Analysing...' : 'Ask'}
                  </button>
                </div>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', background: 'rgba(0,0,0,0.02)', borderRadius: '1rem', minHeight: '150px' }}>
                {chatLoading ? (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      style={{ width: '30px', height: '30px', border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%' }}
                    />
                  </div>
                ) : chatReport ? (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ whiteSpace: 'pre-line', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    {chatReport}
                  </motion.div>
                ) : (
                  <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem' }}>
                    <AlertCircle size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
                    <p>Enter your question above to generate a report.</p>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
};

export default App;
