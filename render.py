import os
import arrow
import requests
import json
print(f"API_KEY 是否在环境变量中: {'API_KEY' in os.environ}")

def Data_parsing(jsondata):
    data = {}
    for i in jsondata["hours"]:
        BJtime = arrow.get(i['time']).shift(hours=8)
        data[BJtime.format('YYYY-MM-DD HH:mm')] = {
        
            '云量': i['cloudCover']['noaa'],
            '气温': i['airTemperature']['ecmwf'],
            '风向': i['windDirection']['ecmwf'],
            '风速': i['windSpeed']['ecmwf'],
            '阵风风速': i['gust']['ecmwf'],
            '海浪方向': i['swellDirection']['meteo'],
            '海浪高度': i['swellHeight']['meteo']
        }
    return data

def get_weather():
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("❌ 警告：未找到 API_KEY 环境变量！")
    else:
        print(f"✅ 成功读取 API_KEY，长度为: {len(api_key)}")
    # Get first hour of today
    start = arrow.now().floor('day')

    # Get last hour of today
    end = arrow.now().ceil('day')

    response = requests.get(
        'https://api.stormglass.io/v2/weather/point',
        params={
            'lat': 39.895595, 
            'lng': 119.551064,
            'params': ','.join(['cloudCover', 'rain','airTemperature','windDirection','gust','windSpeed','swellDirection','swellHeight']),
            'start':start.to('UTC').timestamp(), # Convert to UTC timestamp
            'end': end.shift(days=4).to('UTC').timestamp()# Convert to UTC timestamp
        },
        headers={
            'Authorization': api_key
        }
    )

    # Do something with response data.
    json_data = response.json()

    #print(json_data)
    return json_data

def generate_html_preview(weather_data):
    #json_path = 'weather_data.json'
    output_path = 'index.html'
    
    #if not os.path.exists(json_path):
    #    print(f"Error: {json_path} not found.")
    #    return

    #with open(json_path, 'r', encoding='utf-8') as f:
    #    weather_data = json.load(f)

    # HTML Template - Refined for Integrated Date & Chinese Labels
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>风浪矩阵</title>
    <style>
        :root {
            --bg-ocean: #0c4a6e;
            --bg-deep: #083344;
            --sunshine: #fde047;
            --energy-orange: #f97316;
            --water-cyan: #22d3ee;
            --text-bright: #ffffff;
            --text-dim: #bae6fd;
            --border-soft: rgba(255, 255, 255, 0.1);
            --row-h: 34px;
            --header-h: 40px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background: linear-gradient(135deg, var(--bg-ocean), var(--bg-deep)); 
            color: var(--text-bright); 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            font-size: 13px;
        }

        .dashboard { max-width: 600px; margin: 0 auto; padding-bottom: 50px; background: rgba(0, 0, 0, 0.1); }
        
        header { 
            padding: 15px 12px; 
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-soft);
        }
        h1 { font-size: 1.1rem; font-weight: 800; color: var(--sunshine); }
        #sub-header { font-size: 0.7rem; color: var(--text-dim); margin-top: 2px; }

        .v-grid { display: flex; flex-direction: column; width: 100%; }
        
        /* Integrated Sticky Header */
        .v-header {
            display: flex;
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(12, 74, 110, 0.98);
            backdrop-filter: blur(12px);
            border-bottom: 2px solid var(--sunshine);
            height: var(--header-h);
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .v-row { display: flex; border-bottom: 1px solid var(--border-soft); height: var(--row-h); align-items: stretch; position: relative; }
        .v-cell { 
            flex: 1; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            border-right: 1px solid var(--border-soft);
            position: relative;
            min-width: 0;
        }
        .v-cell:last-child { border-right: none; }

        .h-cell { font-size: 0.55rem; font-weight: 900; color: var(--text-dim); text-align: center; line-height: 1.1; }
        .h-date-time { flex: 1.6; display: flex; flex-direction: column; justify-content: center; background: transparent; }
        .h-date { color: var(--sunshine); font-size: 0.65rem; width: 100%; }

        .val-text { 
            position: relative;
            z-index: 10;
            font-family: 'Inter', monospace; 
            font-weight: 900; 
            font-size: 0.72rem; 
            text-shadow: 0 1px 3px rgba(0,0,0,0.6);
        }
        
        .flow-box { width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 1; pointer-events: none; }
        .flow-svg { width: 100%; height: 100%; display: block; overflow: visible; }

        .arrow-icon { font-size: 0.9rem; z-index: 10; font-weight: bold; }

        /* Column Specific Flex */
        .col-dt { flex: 1.2; } /* Combined Date/Time Column */
        .col-c { flex: 0.85; }
        .col-w { flex: 1; }
        .col-d { flex: 0.85; }

        /* Day transition indicator (not a full row divider) */
        .day-mark { border-top: 2px solid var(--sunshine) !important; }
    </style>
</head>
<body>
    <div class="dashboard">
        <header>
            <h1>风浪矩阵</h1>
            <p id="sub-header">金梦海湾</p>
        </header>

        <div class="v-grid" id="main-grid">
            <!-- Integrated Header -->
            <div class="v-header">
                <div class="v-cell h-cell h-date-time col-dt">
                    <div id="sticky-date" class="h-date">--月--日</div>
                    
                </div>
                <div class="v-cell h-cell col-c">云量<br>(%)</div>
                <div class="v-cell h-cell col-w">气温<br>(℃)</div>
                <div class="v-cell h-cell col-d">风向</div>
                <div class="v-cell h-cell col-w">阵风<br>(m/s)</div>
                <div class="v-cell h-cell col-w">风速<br>(m/s)</div>
                <div class="v-cell h-cell col-d">波向</div>
                <div class="v-cell h-cell col-w">波高<br>(m)</div>
            </div>
        </div>
    </div>

    <script>
        const weatherData = {DATA_PLACEHOLDER};

        function interpolateColor(c1, c2, f) {
            const h = c => parseInt(c, 16);
            const r1 = h(c1.substring(1,3)), g1 = h(c1.substring(3,5)), b1 = h(c1.substring(5,7));
            const r2 = h(c2.substring(1,3)), g2 = h(c2.substring(3,5)), b2 = h(c2.substring(5,7));
            return `#${[Math.round(r1+(r2-r1)*f), Math.round(g1+(g2-g1)*f), Math.round(b1+(b2-b1)*f)].map(x=>x.toString(16).padStart(2,'0')).join('')}`;
        }

        function getColor(metric, val) {
            const scales = {
                temp: [{v:-10,c:'#0ea5e9'}, {v:0,c:'#22d3ee'}, {v:10,c:'#fbbf24'}, {v:25,c:'#f97316'}],
                wind: [{v:0,c:'#38bdf8'}, {v:5,c:'#22d3ee'}, {v:10,c:'#fde047'}, {v:20,c:'#ef4444'}],
                cloud: [{v:0,c:'#e0f2fe'}, {v:50,c:'#7dd3fc'}, {v:100,c:'#334155'}],
                swell: [{v:0,c:'#38bdf8'}, {v:1,c:'#22d3ee'}, {v:2,c:'#fde047'}, {v:4,c:'#f97316'}]
            };
            const s = scales[metric] || scales['wind'];
            if (val <= s[0].v) return s[0].c;
            if (val >= s[s.length-1].v) return s[s.length-1].c;
            for (let i=0; i<s.length-1; i++) {
                if (val >= s[i].v && val <= s[i+1].v) return interpolateColor(s[i].c, s[i+1].c, (val-s[i].v)/(s[i+1].v-s[i].v));
            }
            return s[0].c;
        }

        const metrics = [
            { mk: 'cloud', g: v => v['云量'], n: v => v },
            { mk: 'temp', g: v => v['气温'], n: v => Math.min(100, Math.max(10, ((v+15)/35)*100)) },
            { mk: 'dir', g: v => v['风向'], dir: true },
            { mk: 'wind', g: v => v['阵风风速'], n: v => Math.min(100, (v/15)*100), colorTag: 'wind' },
            { mk: 'wind', g: v => v['风速'], n: v => Math.min(100, (v/10)*100) },
            { mk: 'sdir', g: v => v['海浪方向'], dir: true },
            { mk: 'swell', g: v => v['海浪高度'], n: v => Math.min(100, (v/4)*100) }
        ];

        function renderVertical() {
            const grid = document.getElementById('main-grid');
            const stickyDate = document.getElementById('sticky-date');
            const keys = Object.keys(weatherData).sort();
            
            // Intersection Observer to update Date in Header
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const dateText = entry.target.getAttribute('data-date');
                        if (dateText) stickyDate.innerText = dateText;
                    }
                });
            }, { 
                rootMargin: '-50px 0px -80% 0px', // Trigger near the top
                threshold: 0 
            });

            keys.forEach((k, idx) => {
                const [date, time] = k.split(' ');
                const vals = weatherData[k];
                const prevK = keys[idx-1];
                const isNewDay = !prevK || prevK.split(' ')[0] !== date;

                const row = document.createElement('div');
                row.className = 'v-row' + (isNewDay ? ' day-mark' : '');
                row.setAttribute('data-date', date);
                observer.observe(row);

                // Combined Date/Time cell - only show time but anchor date
                const tCell = document.createElement('div');
                tCell.className = 'v-cell col-dt';
                tCell.innerHTML = `<span class="val-text" style="color:var(--energy-orange)">${time}</span>`;
                row.appendChild(tCell);

                metrics.forEach(m => {
                    const cell = document.createElement('div');
                    cell.className = `v-cell ${m.dir ? 'col-d' : 'col-w'}`;
                    const val = m.g(vals) || 0;

                    if (m.dir) {
                        cell.innerHTML = `
                            <span class="arrow-icon" style="transform:rotate(${(val+180)%360}deg); color: var(--sunshine)">↑</span>
                            <div class="val-text" style="font-size: 0.65rem; color: var(--text-dim)">${val.toFixed(0)}°</div>
                        `;
                    } else {
                        const curW = m.n(val);
                        const prevW = idx > 0 ? m.n(m.g(weatherData[keys[idx-1]]) || 0) : curW;
                        const nextW = idx < keys.length-1 ? m.n(m.g(weatherData[keys[idx+1]]) || 0) : curW;
                        const p1 = (prevW + curW) / 2;
                        const p2 = (curW + nextW) / 2;
                        const d = `M 0 0 L ${p1} 0 Q ${curW} 50, ${p2} 100 L 0 100 Z`;
                        const clr = getColor(m.colorTag || m.mk, val);
                        
                        cell.innerHTML = `
                            <div class="flow-box">
                                <svg class="flow-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
                                    <path d="${d}" fill="${clr}" opacity="0.65" />
                                </svg>
                            </div>
                            <div class="val-text">${val.toFixed(m.mk==='cloud'?0:1)}</div>
                        `;
                    }
                    row.appendChild(cell);
                });

                grid.appendChild(row);
            });
        }

        document.addEventListener('DOMContentLoaded', renderVertical);
    </script>
</body>
</html>"""

    html_content = html_template.replace("{DATA_PLACEHOLDER}", json.dumps(weather_data, ensure_ascii=False, indent=4))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Success: {output_path} generated with integrated date and Chinese labels.")

if __name__ == "__main__":
    weather_data = Data_parsing(get_weather())
    #print(weather_data)
    generate_html_preview(weather_data)












