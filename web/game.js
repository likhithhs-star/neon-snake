const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

const scoreEl = document.getElementById("score");
const bestEl = document.getElementById("best");
const levelEl = document.getElementById("level");
const speedEl = document.getElementById("speed");

const overlay = document.getElementById("overlay");
const message = document.getElementById("message");
const startButton = document.getElementById("startButton");

const GRID = 30;

let cols = 30;
let rows = 25;
let cell = 20;

let snake = [];
let food = { x: 15, y: 12 };

let direction = { x: 1, y: 0 };
let nextDirection = { x: 1, y: 0 };

let score = 0;
let best = Number(localStorage.getItem("neonSnakeBest") || 0);

let level = 1;
let speed = 4.5;

let running = false;
let paused = false;
let gameOver = false;

let lastTime = 0;
let accumulator = 0;

bestEl.textContent = best;

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();

  canvas.width = Math.floor(rect.width * window.devicePixelRatio);
  canvas.height = Math.floor(rect.height * window.devicePixelRatio);

  ctx.setTransform(
    window.devicePixelRatio,
    0,
    0,
    window.devicePixelRatio,
    0,
    0
  );

  cell = Math.min(
    rect.width / cols,
    rect.height / rows
  );
}

function resetGame() {
  snake = [
    { x: 12, y: 12 },
    { x: 11, y: 12 },
    { x: 10, y: 12 },
    { x: 9, y: 12 }
  ];

  direction = { x: 1, y: 0 };
  nextDirection = { x: 1, y: 0 };

  score = 0;
  level = 1;
  speed = 4.5;

  scoreEl.textContent = score;
  levelEl.textContent = level;
  speedEl.textContent = speed.toFixed(1) + "x";

  placeFood();

  accumulator = 0;
  gameOver = false;
}

function startGame() {
  resetGame();

  running = true;
  paused = false;

  overlay.style.display = "none";
}

function endGame() {
  running = false;
  gameOver = true;

  if (score > best) {
    best = score;
    localStorage.setItem("neonSnakeBest", best);
    bestEl.textContent = best;
  }

  message.textContent = `GAME OVER — SCORE ${score}`;
  startButton.textContent = "PLAY AGAIN";
  overlay.style.display = "flex";
}

function togglePause() {
  if (!running || gameOver) return;

  paused = !paused;

  if (paused) {
    message.textContent = "GAME PAUSED";
    startButton.textContent = "RESUME";
    overlay.style.display = "flex";
  } else {
    overlay.style.display = "none";
  }
}

function placeFood() {
  let valid = false;

  while (!valid) {
    food.x = Math.floor(Math.random() * cols);
    food.y = Math.floor(Math.random() * rows);

    valid = !snake.some(
      part => part.x === food.x && part.y === food.y
    );
  }
}

function setDirection(x, y) {
  if (direction.x + x === 0 && direction.y + y === 0) {
    return;
  }

  nextDirection = { x, y };

  if (!running) {
    startGame();
    nextDirection = { x, y };
    direction = { x, y };
  }
}

function update() {
  direction = nextDirection;

  const head = {
    x: snake[0].x + direction.x,
    y: snake[0].y + direction.y
  };

  // Wall wrapping
  if (head.x < 0) head.x = cols - 1;
  if (head.x >= cols) head.x = 0;
  if (head.y < 0) head.y = rows - 1;
  if (head.y >= rows) head.y = 0;

  // Self collision
  if (
    snake.some(
      part => part.x === head.x && part.y === head.y
    )
  ) {
    endGame();
    return;
  }

  snake.unshift(head);

  if (head.x === food.x && head.y === food.y) {
    score++;

    level = Math.floor(score / 3) + 1;
    speed = Math.min(12, 4.5 + (level - 1) * 0.55);

    scoreEl.textContent = score;
    levelEl.textContent = level;
    speedEl.textContent = speed.toFixed(1) + "x";

    if (score > best) {
      best = score;
      bestEl.textContent = best;
      localStorage.setItem("neonSnakeBest", best);
    }

    placeFood();
  } else {
    snake.pop();
  }
}

function drawBackground(width, height) {
  ctx.fillStyle = "#030609";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(0,255,157,0.055)";
  ctx.lineWidth = 1;

  for (let x = 0; x <= width; x += cell) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }

  for (let y = 0; y <= height; y += cell) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function drawSnake() {
  snake.forEach((part, index) => {
    const px = part.x * cell;
    const py = part.y * cell;

    const padding = Math.max(2, cell * 0.08);
    const size = cell - padding * 2;

    ctx.shadowBlur = index === 0 ? 18 : 10;
    ctx.shadowColor = "rgba(0,255,157,0.55)";

    ctx.fillStyle =
      index === 0 ? "#63ffc2" : "#00d989";

    ctx.beginPath();
    ctx.roundRect(
      px + padding,
      py + padding,
      size,
      size,
      cell * 0.24
    );
    ctx.fill();

    ctx.shadowBlur = 0;
  });

  drawHeadDetails();
}

function drawHeadDetails() {
  const head = snake[0];

  const cx = head.x * cell + cell / 2;
  const cy = head.y * cell + cell / 2;

  let eye1;
  let eye2;

  if (direction.x !== 0) {
    eye1 = {
      x: cx + direction.x * cell * 0.18,
      y: cy - cell * 0.18
    };

    eye2 = {
      x: cx + direction.x * cell * 0.18,
      y: cy + cell * 0.18
    };
  } else {
    eye1 = {
      x: cx - cell * 0.18,
      y: cy + direction.y * cell * 0.18
    };

    eye2 = {
      x: cx + cell * 0.18,
      y: cy + direction.y * cell * 0.18
    };
  }

  ctx.fillStyle = "#06100c";

  ctx.beginPath();
  ctx.arc(eye1.x, eye1.y, cell * 0.055, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.arc(eye2.x, eye2.y, cell * 0.055, 0, Math.PI * 2);
  ctx.fill();
}

function drawFood(time) {
  const cx = food.x * cell + cell / 2;
  const cy = food.y * cell + cell / 2;

  const pulse = 1 + Math.sin(time * 0.008) * 0.08;
  const radius = cell * 0.28 * pulse;

  ctx.shadowBlur = 22;
  ctx.shadowColor = "rgba(255,49,88,0.75)";
  ctx.fillStyle = "#ff3158";

  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();

  ctx.shadowBlur = 0;

  ctx.fillStyle = "#ff9caf";
  ctx.beginPath();
  ctx.arc(
    cx - radius * 0.3,
    cy - radius * 0.3,
    radius * 0.25,
    0,
    Math.PI * 2
  );
  ctx.fill();
}

function draw(time) {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  drawBackground(width, height);
  drawFood(time);
  drawSnake();
}

function gameLoop(time) {
  const delta = time - lastTime;
  lastTime = time;

  if (running && !paused) {
    accumulator += delta;

    const interval = 1000 / speed;

    while (accumulator >= interval) {
      update();
      accumulator -= interval;
    }
  }

  draw(time);
  requestAnimationFrame(gameLoop);
}

window.addEventListener("resize", resizeCanvas);

window.addEventListener("keydown", event => {
  const key = event.key.toLowerCase();

  if (
    ["arrowup", "arrowdown", "arrowleft", "arrowright", " "].includes(key)
  ) {
    event.preventDefault();
  }

  if (key === "arrowup" || key === "w") {
    setDirection(0, -1);
  } else if (key === "arrowdown" || key === "s") {
    setDirection(0, 1);
  } else if (key === "arrowleft" || key === "a") {
    setDirection(-1, 0);
  } else if (key === "arrowright" || key === "d") {
    setDirection(1, 0);
  } else if (key === " ") {
    togglePause();
  } else if (key === "r") {
    startGame();
  } else if (key === "escape") {
    running = false;
    paused = false;
    message.textContent = "Press any arrow key or WASD to start";
    startButton.textContent = "START GAME";
    overlay.style.display = "flex";
  }
});

startButton.addEventListener("click", () => {
  if (paused) {
    togglePause();
  } else {
    startGame();
  }
});

resetGame();
resizeCanvas();
requestAnimationFrame(gameLoop);
