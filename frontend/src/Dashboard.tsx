import { useEffect, useState } from 'react'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
)

interface ScoreBucket {
  bucket: string
  count: number
}

interface TimelinePoint {
  date: string
  submissions: number
}

interface PassRateRow {
  task: string
  avg_score: number
  attempts: number
}

interface DashboardData {
  scores: ScoreBucket[]
  timeline: TimelinePoint[]
  passRates: PassRateRow[]
}

type DashboardState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: DashboardData }

const LAB_OPTIONS = ['lab-01', 'lab-02', 'lab-03', 'lab-04', 'lab-05', 'lab-06']

interface DashboardProps {
  token: string
}

async function fetchJson<T>(url: string, token: string): Promise<T> {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    throw new Error(`Request failed for ${url}: HTTP ${response.status}`)
  }

  return (await response.json()) as T
}

function Dashboard({ token }: DashboardProps) {
  const [selectedLab, setSelectedLab] = useState('lab-04')
  const [state, setState] = useState<DashboardState>({ status: 'loading' })

  function handleLabChange(nextLab: string) {
    setState({ status: 'loading' })
    setSelectedLab(nextLab)
  }

  useEffect(() => {
    let cancelled = false

    Promise.all([
      fetchJson<ScoreBucket[]>(`/analytics/scores?lab=${selectedLab}`, token),
      fetchJson<TimelinePoint[]>(`/analytics/timeline?lab=${selectedLab}`, token),
      fetchJson<PassRateRow[]>(`/analytics/pass-rates?lab=${selectedLab}`, token),
    ])
      .then(([scores, timeline, passRates]) => {
        if (cancelled) return
        setState({ status: 'success', data: { scores, timeline, passRates } })
      })
      .catch((error: unknown) => {
        if (cancelled) return
        const message =
          error instanceof Error ? error.message : 'Unknown dashboard error'
        setState({ status: 'error', message })
      })

    return () => {
      cancelled = true
    }
  }, [selectedLab, token])

  const scoreChartData =
    state.status === 'success'
      ? {
          labels: state.data.scores.map((entry) => entry.bucket),
          datasets: [
            {
              label: 'Students',
              data: state.data.scores.map((entry) => entry.count),
              backgroundColor: ['#d95f02', '#f1a340', '#92c5de', '#4393c3'],
              borderRadius: 10,
            },
          ],
        }
      : null

  const timelineChartData =
    state.status === 'success'
      ? {
          labels: state.data.timeline.map((entry) => entry.date),
          datasets: [
            {
              label: 'Submissions',
              data: state.data.timeline.map((entry) => entry.submissions),
              borderColor: '#0b6e4f',
              backgroundColor: 'rgba(11, 110, 79, 0.2)',
              tension: 0.25,
              fill: true,
            },
          ],
        }
      : null

  return (
    <section className="dashboard-shell">
      <div className="dashboard-toolbar">
        <div>
          <p className="eyebrow">Analytics</p>
          <h2>Learning dashboard</h2>
        </div>

        <label className="lab-picker">
          <span>Lab</span>
          <select
            value={selectedLab}
            onChange={(event) => handleLabChange(event.target.value)}
          >
            {LAB_OPTIONS.map((labId) => (
              <option key={labId} value={labId}>
                {labId}
              </option>
            ))}
          </select>
        </label>
      </div>

      {state.status === 'loading' && (
        <div className="dashboard-status">Loading dashboard data...</div>
      )}

      {state.status === 'error' && (
        <div className="dashboard-status dashboard-status-error">
          {state.message}
        </div>
      )}

      {state.status === 'success' && scoreChartData && timelineChartData && (
        <div className="dashboard-grid">
          <article className="panel chart-panel">
            <div className="panel-header">
              <h3>Score distribution</h3>
              <p>How attempts are distributed across score buckets.</p>
            </div>
            <Bar
              data={scoreChartData}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </article>

          <article className="panel chart-panel">
            <div className="panel-header">
              <h3>Submission timeline</h3>
              <p>Attempts grouped by day for the selected lab.</p>
            </div>
            <Line
              data={timelineChartData}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </article>

          <article className="panel table-panel">
            <div className="panel-header">
              <h3>Pass rates by task</h3>
              <p>Average score and number of attempts for each task.</p>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Average score</th>
                  <th>Attempts</th>
                </tr>
              </thead>
              <tbody>
                {state.data.passRates.map((row) => (
                  <tr key={row.task}>
                    <td>{row.task}</td>
                    <td>{row.avg_score.toFixed(1)}</td>
                    <td>{row.attempts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </article>
        </div>
      )}
    </section>
  )
}

export default Dashboard
