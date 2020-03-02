let waveHistory = [];
let time = 0;
let lerpedLast = 0;
let lerpGranularity = 0.1;

let data = [];


function setup() {
  createCanvas(600, 400);
  startSocket()
}


function draw() {
  background(50);

  //let simiVal = stubGetData();
  let dilated = timeDilation(1, data)
  if (dilated) {
    let simiVal = dilated;
    var lerpedCurrent = lerp(lerpedLast, simiVal, lerpGranularity)
  } else {
    var lerpedCurrent = lerp(lerpedLast, lerpedLast, lerpGranularity)
  }  
  renderWave(lerpedCurrent);
  lerpedLast = lerpedCurrent;
}



// # Just get data from index 0
function stubGetData(){
  if (data.length > 0) {
    return data.shift();
  } else {
    return 0;
  }
}


function timeDilation(factor, data){ // higher factor -> slower time passed
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
  return total / factor ;
}

function renderWave(simiVal){

  // # Create sine.
  translate(0,200);
  waveHistory.unshift(simiVal);
  // # Draw
  beginShape();
  noFill();
  stroke(simiVal,0,simiVal)
  for (let i = 0; i < waveHistory.length; i++) {
    let xPos = waveHistory.length - i
    vertex(xPos, waveHistory[i]);
  }
  endShape();
  
  if (waveHistory.length > width / 2) {
    waveHistory.pop()
  }
  
}

// TODO: just make the color permanent.
class colorPoint{
  constructor(value) {
    this.value = value
    this.position = positionVal
  }
  caclColor(val){
    this.color = (colorVal,colorVal/2 ,colorVal)
  }
  render(){
    vertex(xPos, waveHistory[i]);
  }
}


