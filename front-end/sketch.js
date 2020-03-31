let data = []; // # Data from network.
let dataMultiplier = 2; // # Aplify values.
let waveHistory = []; // # ColorPoint history.

let lerpedLast = 0;
let lerpGranularity = 0.1; // # Smoothness between data values

let dilation = 1; // # Dilates time. Higher val = slower time.
let colorHeightAdjustment = 50; // # Higher means lower threshold for color.



function setup() {
  createCanvas(600, 400);
  startSocket();
  
}

function draw() {
  background(50);

  // Data generation for tests
  // if (random(10) < 1) {
  //   data.push(random(-100,0));
  // }

  
  // # Do time-dilation (slower/faster value read)
  //let dilated = timeDilation(dilation, data)
  let dilated = timeDilation(dilation, data);
  
  // # Do potential lerping
  if (dilated) {
    var lerpedCurrent = lerp(lerpedLast, dilated, lerpGranularity)
  } else {
    var lerpedCurrent = lerp(lerpedLast, lerpedLast, lerpGranularity)
  }
  lerpedLast = lerpedCurrent;
  
  // # Visualise
  renderWave(lerpedCurrent);
  
  
}


function timeDilation(factor, data){ // # higher factor -> slower time passed
  // # Clamp 0 <-> data.length
  if (factor < 0 ) { factor = 1}
  if (factor > data.length) {
    //factor = data.length # it will just take everything at once :<
    return null
  }

  // # Do collection; average.
  let total = 0
  for (let i = 0; i < factor; i++) {
    total += data.shift();
  }
  return total / factor;
}

function renderWave(simiVal){

  translate(0,200);
  
  // # Create new  
  let colorPoint = new ColorPoint(simiVal);
  waveHistory.unshift(colorPoint);
 
  
  for (let i = 0; i < waveHistory.length; i++) {
    // # Adjust xPosition to account for value scaling (time dilation).
    
    if (i > 0) { // # For the purpose of connecting vertices.

      let xPosA = (waveHistory.length - i) / dilation
      let yPosA = waveHistory[i].value;
      
      let xPosB = (waveHistory.length - i - 1) / dilation
      let yPosB = waveHistory[i-1].value;
      
      let currentColor = waveHistory[i].getColor(colorHeightAdjustment)
      
      stroke(currentColor)
      line(xPosB, yPosB, xPosA, yPosA)
    }
  }
  
  // # Clear old.
  if (waveHistory.length / dilation > width - width/10) {
    waveHistory.pop()
  }
  // # Debug
  console.log("datalist: " + data.length + " | wavehistory: " + waveHistory.length)
  
}

class ColorPoint{
  constructor(value) {
    this.value = value
  }  
  getColor(colorAdjustment) {
  return [colorAdjustment-this.value, 0, colorAdjustment-this.value]
  }
}



