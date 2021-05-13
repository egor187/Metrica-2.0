import { subDays } from "date-fns";

console.log("hello world");

function isoDayOfWeek(dt) {
  let wd = dt.getDay(); // 0..6, from sunday
  wd = ((wd + 6) % 7) + 1; // 1..7 from monday
  return "" + wd; // string so it gets parsed
}

function makeScoresByDateMap(sessions) {
  return sessions.reduce((mapByDate, session) => {
    const date = new Date(session.date).toISOString().substr(0, 10);
    mapByDate[date] = mapByDate.hasOwnProperty(date)
      ? {
          totalScore: mapByDate[date].totalScore + session.score,
          sessions: mapByDate[date].sessions + 1,
        }
      : { totalScore: session.score, sessions: 1 };
    return mapByDate;
  }, {});
}

function generateData(sessions) {
  const scoresByDateMap = makeScoresByDateMap(sessions);

  const data = [];
  const end = new Date();
  let start = subDays(end, 90);

  while (start <= end) {
    const iso = start.toISOString().substr(0, 10);
    data.push({
      x: iso,
      y: isoDayOfWeek(start),
      d: iso,
      totalScore: scoresByDateMap[iso] ? scoresByDateMap[iso].totalScore : 0,
      sessions: scoresByDateMap[iso] ? scoresByDateMap[iso].sessions : 0,
    });
    start = new Date(start.setDate(start.getDate() + 1));
  }

  return data;
}

function initUserChart(gameData) {
  const ctx = document.getElementById("chart-area");
  // For one game only for now, but need to have this charts for every game
  const sessions = gameData[0].sessions;
  const data = generateData(sessions);
  console.log(data);
  const userChart = new Chart(ctx, {
    type: "matrix",
    data: {
      datasets: [
        {
          label: "My Matrix",
          data,
          backgroundColor(c) {
            const value = c.dataset.data[c.dataIndex].totalScore;
            const alpha = value ? value : 0.1;
            return Chart.helpers.color("green").alpha(alpha).rgbString();
          },
          width(c) {
            return 35;
          },
          height(c) {
            return 30;
          },
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          displayColors: false,
          callbacks: {
            title() {
              return "";
            },
            label(context) {
              const v = context.dataset.data[context.dataIndex];
              return [
                "Date: " + v.d,
                "Sessions this day: " + v.sessions,
                "Total score: " + v.totalScore,
              ];
            },
          },
        },
      },
      scales: {
        x: {
          type: "time",
          left: "left",
          offset: true,
          time: {
            unit: "month",
            round: "week",
            isoWeekDay: 1,
            displayFormats: {
              month: "MMM",
            },
          },
          ticks: {
            maxRotation: 0,
            autoSkip: true,
            padding: 1,
          },
          grid: {
            display: false,
            drawBorder: false,
            tickMarkLength: 0,
          },
        },
        y: {
          type: "time",
          offset: true,
          time: {
            unit: "day",
            parser: "i",
            displayFormats: {
              day: "iiiiii",
            },
          },
          reverse: true,
          ticks: {
            source: "data",
            padding: 4,
          },
          grid: {
            display: false,
            drawBorder: false,
            tickMarkLength: 0,
          },
        },
      },
    },
  });
}

window.initUserChart = initUserChart;
