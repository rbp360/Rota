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
  const [selectedDay, setSelectedDay] = useState('Thursday');
  const [availableStaff, setAvailableStaff] = useState([]);
  const [staffList, setStaffList] = useState([]);

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

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
        const res = await axios.get(`http://localhost:8000/availability?periods=${periods.join(',')}&day=${selectedDay}`);
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
        const res = await axios.get('http://localhost:8000/staff');
        setStaffList(res.data.map(s => s.name));
      } catch (err) {
        console.error("Failed to fetch staff:", err);
      }
    };
    fetchStaff();
  }, []);

  // Helper to ensure an absence record exists in the DB
  const ensureAbsence = async () => {
    if (currentAbsenceId) return currentAbsenceId;

    try {
      const res = await axios.post('http://localhost:8000/absences', null, {
        params: {
          staff_name: absentPerson,
          date: new Date().toISOString().split('T')[0],
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

      const suggestRes = await axios.get(`http://localhost:8000/suggest-cover/${aid}?day=${selectedDay}`);
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

      await axios.post('http://localhost:8000/assign-cover', null, {
        params: {
          absence_id: aid,
          staff_name: staffName,
          periods: periods.join(',')
        }
      });

      setCoveredPeriods(prev => [...new Set([...prev, ...periods])]);
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
        await axios.delete(`http://localhost:8000/unassign-cover`, {
          params: { absence_id: currentAbsenceId, period: p }
        });
        setCoveredPeriods(prev => prev.filter(x => x !== p));
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
    setPeriods([1, 2, 3, 4, 5, 6]);
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
              padding: '1rem 2rem', borderRadius: '2rem', boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
              display: 'flex', alignItems: 'center', gap: '0.5rem'
            }}
          >
            {toast.type === 'success' ? <CheckCircle size={20} /> : (toast.type === 'info' ? <RotateCcw size={20} /> : <AlertCircle size={20} />)}
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem' }}>Rota<span style={{ color: 'var(--primary)' }}>AI</span></h1>
          <p style={{ color: 'var(--text-muted)' }}>Intelligent School Cover Management</p>
        </div>
        <div className="glass" style={{ padding: '0.5rem', display: 'flex', gap: '0.5rem' }}>
          <button onClick={() => setActiveTab('absence')} className={activeTab === 'absence' ? 'btn-primary' : ''} style={{ padding: '0.5rem 1rem' }}>Absence</button>
          <button onClick={() => setActiveTab('rota')} className={activeTab === 'rota' ? 'btn-primary' : ''} style={{ padding: '0.5rem 1rem' }}>Daily Rota</button>
          <button onClick={() => setActiveTab('settings')} className={activeTab === 'settings' ? 'btn-primary' : ''} style={{ padding: '0.5rem 1rem' }}><Settings size={18} /></button>
        </div>
      </header>

      <div className="glass" style={{ padding: '1rem', marginBottom: '2rem', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
        {days.map(d => (
          <button
            key={d}
            onClick={() => { setSelectedDay(d); setCoveredPeriods([]); setCurrentAbsenceId(null); setSuggestions(null); }}
            className={selectedDay === d ? 'btn-primary' : 'glass'}
            style={{ padding: '0.5rem 1.5rem', flex: 1, minWidth: '100px' }}
          >
            {d}
          </button>
        ))}
      </div>

      <main>
        {activeTab === 'absence' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid-cols">
              <div className="glass" style={{ padding: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <UserPlus size={20} color="var(--primary)" /> Who is Absent?
                </h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>Select Staff</label>
                  <select value={absentPerson} onChange={(e) => { setAbsentPerson(e.target.value); setCoveredPeriods([]); setCurrentAbsenceId(null); setSuggestions(null); }}>
                    <option value="">Select a person...</option>
                    {staffList.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div style={{ marginBottom: '2rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>Periods Absent</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
                    {[1, 2, 3, 4, 5, 6].map(p => {
                      const isCovered = coveredPeriods.includes(p);
                      const isSelected = periods.includes(p);
                      return (
                        <button
                          key={p}
                          onClick={() => handlePeriodClick(p)}
                          className="glass"
                          style={{
                            padding: '0.5rem',
                            background: isCovered ? 'var(--accent)' : (isSelected ? 'var(--primary)' : 'transparent'),
                            borderColor: isCovered ? 'var(--accent)' : (isSelected ? 'var(--primary)' : 'var(--border)'),
                            color: 'white',
                            transition: 'all 0.3s ease'
                          }}
                        >
                          {isCovered ? <CheckCircle size={14} style={{ marginRight: '4px' }} /> : ''} P{p}
                        </button>
                      );
                    })}
                  </div>
                  <button
                    onClick={selectAllDay}
                    className="glass"
                    style={{ width: '100%', padding: '0.5rem', background: periods.length === 6 ? 'var(--primary)' : 'rgba(255,255,255,0.05)' }}
                  >
                    Select All Day
                  </button>
                </div>

                <button
                  className="btn-primary"
                  style={{ width: '100%' }}
                  onClick={handleSuggest}
                  disabled={!absentPerson || periods.length === 0}
                >
                  {loading ? 'Analyzing...' : 'Generate AI Suggestions'}
                </button>
              </div>

              <div className="glass" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={20} color="var(--accent)" /> AI Suggestion
                </h3>

                <AnimatePresence>
                  {!suggestions && !loading && (
                    <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)' }}>
                      <AlertCircle size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                      <p>Optionally generate AI suggestions, or just pick from availability below.</p>
                    </div>
                  )}

                  {loading && (
                    <div style={{ margin: 'auto' }}>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        style={{ width: '40px', height: '40px', border: '4px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%' }}
                      />
                    </div>
                  )}

                  {suggestions && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <div className="glass" style={{ padding: '1rem', marginBottom: '1rem', background: 'rgba(255,255,255,0.03)', whiteSpace: 'pre-line', fontSize: '0.875rem', lineHeight: '1.6' }}>
                        {suggestions}
                      </div>
                      <div style={{ marginTop: 'auto', display: 'flex', gap: '1rem' }}>
                        <button className="btn-primary" style={{ flex: 1 }}>Accept AI Selection</button>
                        <button className="glass" style={{ flex: 1, padding: '0.75rem' }}>Refine</button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass" style={{ padding: '2rem' }}>
              <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar size={20} color="var(--primary)" /> Availability Checker
                <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
                  {periods.length > 0 ? `(Click a teacher to assign to P${periods.sort().join(', P')})` : '(Select periods above)'}
                </span>
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                {availableStaff.length > 0 ? (
                  availableStaff.map((s, i) => {
                    const isBusySpecialist = !s.is_free;
                    let bgColor = 'rgba(255,255,255,0.03)';
                    let borderColor = 'var(--border)';
                    let textColor = 'var(--text-main)';

                    if (s.is_priority && s.is_free) {
                      bgColor = 'rgba(99, 102, 241, 0.15)';
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
                        onClick={() => s.is_free && handleAssignCover(s.name)}
                        className="glass"
                        style={{
                          padding: '0.75rem',
                          cursor: s.is_free ? 'pointer' : 'default',
                          background: bgColor,
                          border: `1px solid ${borderColor}`,
                          opacity: s.is_free ? 1 : 0.8
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ fontWeight: '600', color: s.is_priority && s.is_free ? 'var(--primary)' : (isBusySpecialist ? '#ef4444' : 'var(--text-main)') }}>
                            {s.name}
                          </div>
                          {!s.is_free && <span style={{ fontSize: '0.65rem', background: '#ef4444', padding: '1px 5px', borderRadius: '4px', color: 'white' }}>BUSY</span>}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.profile || 'Staff Member'}</div>
                        {!s.is_free && (
                          <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: '#ef4444', fontWeight: '500' }}>
                            Doing: {s.activity}
                          </div>
                        )}
                      </motion.div>
                    );
                  })
                ) : (
                  <p style={{ color: 'var(--text-muted)', gridColumn: '1/-1' }}>
                    {periods.length > 0 ? 'No staff members are free for all selected periods.' : 'Select periods to see who is available.'}
                  </p>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </main>

      <div style={{ position: 'fixed', bottom: '2rem', right: '2rem' }}>
        <button className="btn-primary" style={{ borderRadius: '50%', width: '3.5rem', height: '3.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <MessageSquare />
        </button>
      </div>
    </div>
  );
};

export default App;
