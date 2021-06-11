const ctx = document.getElementById("gamesDetailsChart");

const COLORS = [
  "rgba(255, 99, 132, 0.2)",
  "rgba(54, 162, 235, 0.2)",
  "rgba(255, 206, 86, 0.2)",
  "rgba(75, 192, 192, 0.2)",
  "rgba(153, 102, 255, 0.2)",
  "rgba(255, 159, 64, 0.2)",
];

function getColor(index) {
  return COLORS[index % COLORS.length];
}

const gamesDetailsChart = new Chart(ctx, {
  type: "horizontalBar",
  data: {
    labels: serverData.users.map((user) => user.name),
    datasets: [
      {
        data: serverData.users.map((user) => user.score),
        backgroundColor: ({ dataIndex }) => COLORS[dataIndex % COLORS.length],
      },
    ],
  },
  options: {
    aspectRatio: 6, // This make chart narrow
    legend: false,
    scales: {
      yAxes: [
        {
          gridLines: {
            display: false,
          },
        },
      ],
      xAxes: [
        {
          ticks: {
            beginAtZero: true,
          },
          gridLines: {
            color: "#f2f2f2",
          },
        },
      ],
    },
  },
});
