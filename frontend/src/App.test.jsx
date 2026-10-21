import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App.jsx';

const records = {
  players: [{ id: 1, full_name: 'Test Player', position: 'Centre', jersey_number: 10, status: 'active' }],
  matches: [{ id: 1, opponent: 'Test RFC', date: '2026-04-02', competition_name: 'League', venue: 'Nairobi', status: 'completed', wazimba_score: 26, opponent_score: 12 }],
  training: [{ id: 1, title: 'Defence', date: '2026-04-03', start_time: '17:00', location: 'Pitch' }],
  tournaments: [], announcements: [], seasons: [{ id: 1, name: '2026 Season', status: 'active', start_date: '2026-01-01' }],
  registrations: [], events: [], eventAttendance: [], learning: [], media: [], alumni: [], reviews: [], participations: [], attendance: [], injuries: [],
};
const pathToKey = { '/players/':'players', '/matches/':'matches', '/training-sessions/':'training', '/tournaments/':'tournaments', '/announcements/':'announcements', '/seasons/':'seasons', '/season-registrations/':'registrations', '/team-events/':'events', '/team-event-attendance/':'eventAttendance', '/learning-resources/':'learning', '/media/':'media', '/alumni/':'alumni', '/match-reviews/':'reviews', '/match-participations/':'participations', '/training-attendance/':'attendance', '/injury-records/':'injuries' };
const jsonResponse = (data, status=200) => ({ ok:status<400, status, headers:{get:()=> 'application/json'}, json:async()=>data, blob:async()=>new Blob([JSON.stringify(data)]) });

function mockApi() {
  return vi.fn(async (input, options={}) => {
    const url = new URL(input);
    const path = url.pathname.replace('/api','');
    const method = options.method || 'GET';
    if (path === '/dashboard/') return jsonResponse({active_players:records.players.filter(p=>p.status==='active').length,matches_played:1,wins:1,losses:0,draws:0,win_rate:100,training_sessions:1,next_match:null,next_training:records.training[0],recent_announcements:[]});
    if (path === '/performance/team/') return jsonResponse({matches_played:1,wins:1,losses:0,draws:0,win_rate:100,points_for:26,points_against:12,training_sessions:1,training_attendance_total:1,training_attendance_rate:100,match_results:[{id:1,date:'2026-04-02',opponent:'Test RFC',score_for:26,score_against:12,result:'Win'}]});
    if (path === '/performance/players/') return jsonResponse([{player_id:1,player__full_name:'Test Player',player__position:'Centre',appearances:1,starts:1,minutes:40,tries:2,assists:1,tackles:7,turnovers_won:1,errors:0}]);
    if (path === '/reports/') return jsonResponse({season:null,team:{matches_played:1,wins:1,losses:0,points_for:26},players:[],training_sessions:1,matches:[]});
    if (path === '/reports/csv/') return {ok:true,status:200,headers:{get:()=> 'text/csv'},blob:async()=>new Blob(['report'])};
    const base = Object.keys(pathToKey).find(route=>path.startsWith(route));
    if (!base) return jsonResponse({detail:'Not found'},404);
    const key = pathToKey[base];
    const tail = path.slice(base.length).replace(/\/$/,'');
    if (method === 'GET') return jsonResponse({count:records[key].length,next:null,results:records[key]});
    if (method === 'POST') {
      const row = {...JSON.parse(options.body),id:Math.max(0,...records[key].map(r=>r.id||0))+1};
      records[key].push(row);
      return jsonResponse(row,201);
    }
    const id = Number(tail);
    const index = records[key].findIndex(row=>row.id===id);
    if (index < 0) return jsonResponse({detail:'Not found'},404);
    if (method === 'PATCH') { records[key][index]={...records[key][index],...JSON.parse(options.body)}; return jsonResponse(records[key][index]); }
    if (method === 'DELETE') { records[key].splice(index,1); return {ok:true,status:204,headers:{get:()=>null}}; }
    return jsonResponse({detail:'Not found'},404);
  });
}

describe('Wazimba app interactions', () => {
  beforeEach(() => {
    Object.values(records).forEach(rows=>rows.splice(0,rows.length));
    records.players.push({id:1,full_name:'Test Player',position:'Centre',jersey_number:10,status:'active'});
    records.matches.push({id:1,opponent:'Test RFC',date:'2026-04-02',competition_name:'League',venue:'Nairobi',status:'completed',wazimba_score:26,opponent_score:12});
    records.training.push({id:1,title:'Defence',date:'2026-04-03',start_time:'17:00',location:'Pitch'});
    records.seasons.push({id:1,name:'2026 Season',status:'active',start_date:'2026-01-01'});
    localStorage.setItem('wazimbaToken','test-token');
    localStorage.setItem('wazimbaUser','Test Admin');
    localStorage.setItem('wazimbaStaff','true');
    global.fetch=mockApi();
    window.confirm=vi.fn(()=>true);
    URL.createObjectURL=vi.fn(()=> 'blob:test');
    URL.revokeObjectURL=vi.fn();
    HTMLAnchorElement.prototype.click=vi.fn();
  });
  afterEach(()=>{cleanup();localStorage.clear();vi.restoreAllMocks();});

  it('navigates to team analytics, player performance, and reports using saved API data', async()=>{
    const user=userEvent.setup();render(<App/>);
    await screen.findByText('Test Player');
    await user.click(screen.getByRole('button',{name:'Performance'}));
    expect(await screen.findByText('26')).toBeTruthy();
    await user.click(screen.getByRole('tab',{name:'Player performance'}));
    expect(await screen.findByText('Test Player')).toBeTruthy();
    expect(screen.getByText('2',{selector:'td'})).toBeTruthy();
    await user.click(screen.getByRole('tab',{name:'Reports'}));
    await user.click(await screen.findByRole('button',{name:'Export CSV'}));
    await waitFor(()=>expect(global.fetch.mock.calls.some(([url])=>String(url).includes('/api/reports/csv/'))).toBe(true));
  });

  it('creates, edits, and deletes a player through the UI and REST API', async()=>{
    const user=userEvent.setup();render(<App/>);
    await user.click(await screen.findByRole('button',{name:'Players'}));
    await screen.findByText('Test Player');
    await user.click(screen.getByRole('button',{name:'Add player'}));
    await user.type(screen.getByLabelText('Full name'),'New Player');
    await user.click(screen.getByRole('button',{name:'Save record'}));
    const row=await screen.findByRole('row',{name:/New Player/});
    await user.click(within(row).getByRole('button',{name:'Edit'}));
    const fullName=screen.getByLabelText('Full name');
    await user.clear(fullName);await user.type(fullName,'Updated Player');
    await user.click(screen.getByRole('button',{name:'Save changes'}));
    const updated=await screen.findByRole('row',{name:/Updated Player/});
    await user.click(within(updated).getByRole('button',{name:'Delete'}));
    await waitFor(()=>expect(screen.queryByText('Updated Player')).toBeNull());
    expect(global.fetch.mock.calls.some(([,opts])=>opts?.method==='POST')).toBe(true);
    expect(global.fetch.mock.calls.some(([,opts])=>opts?.method==='PATCH')).toBe(true);
    expect(global.fetch.mock.calls.some(([,opts])=>opts?.method==='DELETE')).toBe(true);
  });

  it('links a match row to player-stat recording and handles list navigation', async()=>{
    const user=userEvent.setup();render(<App/>);
    await user.click(await screen.findByRole('button',{name:'Matches'}));
    const row=await screen.findByRole('row',{name:/Test RFC/});
    await user.click(within(row).getByRole('button',{name:'Record stats'}));
    expect(await screen.findByRole('heading',{name:'Record match statistics'})).toBeTruthy();
    expect(screen.getByLabelText('Match').value).toBe('1');
    await user.click(screen.getByRole('button',{name:'Cancel'}));
    await user.click(screen.getByRole('button',{name:'Training'}));
    const session=await screen.findByRole('row',{name:/Defence/});
    await user.click(within(session).getByRole('button',{name:'Attendance'}));
    expect(await screen.findByRole('heading',{name:'Record training attendance'})).toBeTruthy();
    await user.selectOptions(screen.getByLabelText('Player'),'1');
    await user.click(screen.getByLabelText('Attended'));
    await user.click(screen.getByRole('button',{name:'Save record'}));
    await waitFor(()=>expect(records.attendance).toHaveLength(1));
  });

  it('records team event attendance against an event and player', async()=>{
    records.events.push({id:1,title:'Team meeting',date:'2026-04-05',category:'meeting',location:'Club'});
    const user=userEvent.setup();render(<App/>);
    await user.click(await screen.findByRole('button',{name:'Team events'}));
    const row=await screen.findByRole('row',{name:/Team meeting/});
    await user.click(within(row).getByRole('button',{name:'Attendance'}));
    expect(await screen.findByRole('heading',{name:'Record event attendance'})).toBeTruthy();
    await user.selectOptions(screen.getByLabelText('Player'),'1');
    await user.click(screen.getByLabelText('Attended'));
    await user.click(screen.getByRole('button',{name:'Save record'}));
    await waitFor(()=>expect(records.eventAttendance).toHaveLength(1));
    expect(records.eventAttendance[0].event).toBe(1);
  });

  it('routes every sidebar destination to its intended section', async()=>{
    const user=userEvent.setup();render(<App/>);
    for (const label of ['Seasons','Tournaments','Team events','Injury & welfare','Rules & laws','Tactical learning','Video resources','News & information','Media gallery','Historical archive','Alumni & supporters','Post-match analysis','Reports']) {
      await user.click(await screen.findByRole('button',{name:label}));
      expect(await screen.findByRole('heading',{name:label})).toBeTruthy();
    }
  });

  it('keeps write controls staff-only and explains restricted welfare access', async()=>{
    localStorage.setItem('wazimbaStaff','false');
    const user=userEvent.setup();render(<App/>);
    await user.click(await screen.findByRole('button',{name:'Players'}));
    await screen.findByText('Test Player');
    expect(screen.queryByRole('button',{name:'Add player'})).toBeNull();
    await user.click(screen.getByRole('button',{name:'Injury & welfare'}));
    expect(await screen.findByText(/restricted to authorized team staff/i)).toBeTruthy();
    expect(global.fetch.mock.calls.some(([url])=>String(url).includes('/api/injury-records/'))).toBe(false);
  });

  it('searches the saved match records from the global search box', async()=>{
    const user=userEvent.setup();render(<App/>);
    const search=screen.getByPlaceholderText('Search players, matches...');
    await user.type(search,'Test RFC');
    await user.keyboard('{Enter}');
    expect(await screen.findByRole('heading',{name:'Matches'})).toBeTruthy();
    expect(await screen.findByRole('row',{name:/Test RFC/})).toBeTruthy();
  });

  it('shows API failures and an explicit retry instead of substituting sample records', async()=>{
    global.fetch=vi.fn(()=>Promise.reject(new Error('offline')));
    const user=userEvent.setup();render(<App/>);
    expect(await screen.findByText(/Could not load/)).toBeTruthy();
    expect(screen.getByRole('button',{name:'Retry'})).toBeTruthy();
    await user.click(screen.getByRole('button',{name:'Retry'}));
    expect(await screen.findByText(/Could not load/)).toBeTruthy();
  });
});
