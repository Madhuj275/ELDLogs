import "./LogSheet.css";

const ROWS = [
  { key: "OFF", label: "1. Off Duty" },
  { key: "SB", label: "2. Sleeper Berth" },
  { key: "D", label: "3. Driving" },
  { key: "ON", label: "4. On Duty (not driving)" },
];

const ROW_INDEX = { OFF: 0, SB: 1, D: 2, ON: 3 };

const MARGIN_LEFT = 190;
const MARGIN_RIGHT = 40;
const MARGIN_TOP = 30;
const ROW_HEIGHT = 42;
const CHART_WIDTH = 960;
const HOUR_WIDTH = CHART_WIDTH / 24;

function hourLabel(h) {
  const hh = h % 24;
  if (hh === 0) return "Mid night";
  if (hh === 12) return "Noon";
  return hh > 12 ? String(hh - 12) : String(hh);
}

function formatDate(dateStr) {
  const [y, m, d] = dateStr.split("-");
  return { month: m, day: d, year: y };
}

export default function LogSheet({ log, dayIndex, manifest = {}, route }) {
  const chartHeight = ROWS.length * ROW_HEIGHT;
  const svgWidth = MARGIN_LEFT + CHART_WIDTH + MARGIN_RIGHT;
  const svgHeight = MARGIN_TOP + chartHeight + 30;

  const x = (hour) => MARGIN_LEFT + hour * HOUR_WIDTH;
  const y = (rowKey) => MARGIN_TOP + ROW_INDEX[rowKey] * ROW_HEIGHT + ROW_HEIGHT / 2;

  const sorted = [...log.events].sort((a, b) => a.start_hour - b.start_hour);
  let pathParts = [];
  sorted.forEach((ev, idx) => {
    const startX = x(ev.start_hour);
    const endX = x(ev.end_hour);
    const rowY = y(ev.status);
    if (idx === 0) {
      pathParts.push(`M ${startX} ${rowY}`);
    } else {
      const prevY = y(sorted[idx - 1].status);
      pathParts.push(`L ${startX} ${prevY}`);
      pathParts.push(`L ${startX} ${rowY}`);
    }
    pathParts.push(`L ${endX} ${rowY}`);
  });

  const totals = log.totals;
  const { month, day, year } = formatDate(log.date);

  return (
    <article className="log-sheet">
      <header className="log-sheet__banner">
        <div className="log-sheet__banner-id">
          <span className="log-sheet__eyebrow">Day {dayIndex}</span>
          <h3 className="log-sheet__date">{month}/{day}/{year}</h3>
        </div>
        <div className="log-sheet__totals-quick">
          <span><strong>{totals.driving}</strong>h driving</span>
          <span><strong>{totals.on_duty}</strong>h on-duty</span>
          <span><strong>{totals.sleeper_berth}</strong>h sleeper</span>
          <span><strong>{totals.off_duty}</strong>h off-duty</span>
        </div>
      </header>

      <div className="log-sheet__paper">
        <div className="log-sheet__form-header">
          <div className="log-sheet__form-row">
            <div className="log-sheet__form-cell">
              <label>Driver number</label>
              <div className="log-sheet__form-value">{manifest.driver_number || "N/A"}</div>
            </div>
            <div className="log-sheet__form-cell">
              <label>Driver's initials</label>
              <div className="log-sheet__form-value">{manifest.driver_initials || "\u2014"}</div>
            </div>
            <div className="log-sheet__form-cell log-sheet__form-cell--wide">
              <label>Driver's signature (certifies entries are true &amp; correct)</label>
              <div className="log-sheet__signature">{manifest.driver_name || "Driver on file"}</div>
            </div>
            <div className="log-sheet__form-cell">
              <label>Date</label>
              <div className="log-sheet__form-value log-sheet__form-value--mono">
                {month} / {day} / {year}
              </div>
            </div>
          </div>

          <div className="log-sheet__form-row">
            <div className="log-sheet__form-cell log-sheet__form-cell--wide">
              <label>Vehicle numbers (tractor / trailer)</label>
              <div className="log-sheet__form-value log-sheet__form-value--mono">
                P {manifest.truck_number || "N/A"} &nbsp;/&nbsp; T {manifest.trailer_number || "N/A"}
              </div>
            </div>
            <div className="log-sheet__form-cell">
              <label>Total driving miles today</label>
              <div className="log-sheet__form-value log-sheet__form-value--mono">
                {log.miles_today?.toLocaleString() ?? "0"}
              </div>
            </div>
            <div className="log-sheet__form-cell">
              <label>Total truck mileage today</label>
              <div className="log-sheet__form-value log-sheet__form-value--mono">
                {log.miles_today?.toLocaleString() ?? "0"}
              </div>
            </div>
            <div className="log-sheet__form-cell">
              <label>Co-driver</label>
              <div className="log-sheet__form-value">{manifest.co_driver || "NA"}</div>
            </div>
          </div>

          <div className="log-sheet__form-row">
            <div className="log-sheet__form-cell log-sheet__form-cell--wide">
              <label>Home operating center &amp; address</label>
              <div className="log-sheet__form-value">
                {manifest.home_terminal_address || "\u2014"}
              </div>
            </div>
            <div className="log-sheet__form-cell log-sheet__form-cell--wide">
              <label>Carrier</label>
              <div className="log-sheet__form-value">{manifest.carrier_name || "\u2014"}</div>
            </div>
          </div>
        </div>

        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="log-sheet__svg"
          role="img"
          aria-label={`Duty status grid for ${log.date}`}
        >
          {Array.from({ length: 25 }, (_, h) => (
            <text key={`label-${h}`} x={x(h)} y={MARGIN_TOP - 10} textAnchor="middle" className="log-sheet__hour-label">
              {hourLabel(h)}
            </text>
          ))}

          {Array.from({ length: 24 }, (_, h) => (
            <g key={`grid-${h}`}>
              {[0, 0.25, 0.5, 0.75].map((frac) => (
                <line
                  key={frac}
                  x1={x(h + frac)}
                  x2={x(h + frac)}
                  y1={MARGIN_TOP}
                  y2={MARGIN_TOP + chartHeight}
                  className={frac === 0 ? "log-sheet__grid-hour" : "log-sheet__grid-quarter"}
                />
              ))}
            </g>
          ))}
          <line x1={x(24)} x2={x(24)} y1={MARGIN_TOP} y2={MARGIN_TOP + chartHeight} className="log-sheet__grid-hour" />

          {ROWS.map((row, i) => (
            <g key={row.key}>
              <rect
                x={MARGIN_LEFT}
                y={MARGIN_TOP + i * ROW_HEIGHT}
                width={CHART_WIDTH}
                height={ROW_HEIGHT}
                className={i % 2 === 0 ? "log-sheet__row-even" : "log-sheet__row-odd"}
              />
              <line
                x1={MARGIN_LEFT}
                x2={MARGIN_LEFT + CHART_WIDTH}
                y1={MARGIN_TOP + i * ROW_HEIGHT}
                y2={MARGIN_TOP + i * ROW_HEIGHT}
                className="log-sheet__grid-hour"
              />
              <text
                x={MARGIN_LEFT - 12}
                y={MARGIN_TOP + i * ROW_HEIGHT + ROW_HEIGHT / 2 + 4}
                textAnchor="end"
                className="log-sheet__row-label"
              >
                {row.label}
              </text>
            </g>
          ))}
          <line
            x1={MARGIN_LEFT}
            x2={MARGIN_LEFT + CHART_WIDTH}
            y1={MARGIN_TOP + chartHeight}
            y2={MARGIN_TOP + chartHeight}
            className="log-sheet__grid-hour"
          />

          <path d={pathParts.join(" ")} className="log-sheet__status-line" fill="none" />
        </svg>

        <div className="log-sheet__shipment-row">
          <div><label>Shipper</label><span>{manifest.shipper || "N/A"}</span></div>
          <div><label>Commodity</label><span>{manifest.commodity || "N/A"}</span></div>
          <div><label>Load no.</label><span>{manifest.load_number || "N/A"}</span></div>
        </div>
      </div>

      <div className="log-sheet__remarks">
        <h4>Remarks</h4>
        <ul>
          {sorted.map((ev, idx) => (
            <li key={idx}>
              <span className="log-sheet__remark-time">{ev.clock_start}&ndash;{ev.clock_end}</span>
              <span className={`log-sheet__remark-badge log-sheet__remark-badge--${ev.status}`}>{ev.status}</span>
              <span className="log-sheet__remark-text">
                {ev.label}
                {ev.distance_miles > 0 ? ` (${ev.distance_miles} mi)` : ""}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="log-sheet__recap">
        <div><span>Off duty</span><strong>{totals.off_duty}h</strong></div>
        <div><span>Sleeper berth</span><strong>{totals.sleeper_berth}h</strong></div>
        <div><span>Driving</span><strong>{totals.driving}h</strong></div>
        <div><span>On duty (not driving)</span><strong>{totals.on_duty}h</strong></div>
        <div className="log-sheet__recap-highlight">
          <span>Driving + On duty today</span>
          <strong>{log.total_on_duty_plus_driving}h</strong>
        </div>
      </div>

      <div className="log-sheet__inspection">
        <h4>Post-Trip Inspection Report</h4>
        <p>
          Tractor/trailer: <strong>{manifest.truck_number || "N/A"} / {manifest.trailer_number || "N/A"}</strong>
        </p>
        <label className="log-sheet__checkbox">
          <input type="checkbox" defaultChecked readOnly />
          No defects noted that would affect safe operation
        </label>
        <p className="log-sheet__inspection-signature">
          Driver: {manifest.driver_name || "Driver on file"} &nbsp;&middot;&nbsp; Signature on file
        </p>
      </div>
    </article>
  );
}
