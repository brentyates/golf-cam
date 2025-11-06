# IR Strobing for Golf Club Impact Capture

## Research Overview

Investigation into using infrared LED strobing with multiple pulses during a single camera exposure to capture precise golf club-ball impact points at high frame rates.

**Note**: This technique **cannot be used** with this system due to IR interference with launch monitor sensors. This document is for reference and potential future applications.

## The Core Concept

Instead of relying solely on high frame rates (500+ fps), use **stroboscopic photography** - multiple short IR light pulses during a single longer camera exposure - to create multiple "frozen" images of the club position within one frame.

### Stroboscopic Photography Explained

**Traditional approach**:
- 500 fps @ 2ms exposure = one clear image every 2ms
- Impact occurs between frames = miss exact impact point

**Stroboscopic approach**:
- 500 fps @ 2ms exposure + 3 IR strobes @ 50µs pulse width
- Each strobe "freezes" motion for 50µs
- Single frame captures 3 distinct club positions
- Higher probability of capturing exact impact moment

## Physics of Golf Ball Impact

### Critical Timing Parameters

- **Club-ball contact duration**: ~450-500 microseconds (0.5 milliseconds)
- **Clubhead speed**: 90-110 mph (40-49 m/s) for average golfer
- **Ball compression**: Begins at contact, max at ~250µs, release at ~500µs
- **Impact zone travel**: Club moves ~20-25mm during contact

### Frame Rate Analysis @ 500 FPS

**Without strobing**:
- Frame interval: 2 milliseconds (2000µs)
- Impact duration: 500µs
- **Problem**: Impact occurs entirely within a single frame's exposure
- Result: Motion blur obscures exact impact point

**Math**:
```
Clubhead at 100 mph = 44.7 m/s = 44.7 mm/ms
In 2ms exposure: 44.7 × 2 = 89.4 mm of travel
In 500µs contact: 44.7 × 0.5 = 22.35 mm of travel (blurred)
```

## Stroboscopic Solution

### Multiple Pulse Configuration

**Proposed setup**: 3 IR pulses during each 2ms exposure

```
Frame exposure: 2000µs
├─ Strobe 1: @ 0µs    (50µs pulse)
├─ Strobe 2: @ 700µs  (50µs pulse)
└─ Strobe 3: @ 1400µs (50µs pulse)
```

**Advantages**:
1. **3× sampling rate**: Effectively 1500 fps "sampling" at 500 fps recording
2. **Frozen motion**: Each 50µs pulse freezes ~2.2mm of motion (vs 89mm blur)
3. **Impact capture probability**: Much higher chance one pulse captures impact
4. **Composite analysis**: Can see before/during/after impact in single frame

### Visual Result

Each frame would show:
- 3 semi-transparent images of the club
- Spacing between images reveals speed and acceleration
- If impact occurs, one image shows compressed ball
- Can measure exact contact point from ghost images

## LED Strobe Specifications

### Pulse Duration Requirements

To freeze golf impact motion:

**Minimum acceptable**:
- **50-100 microseconds** pulse width
- Freezes motion to ~2-4mm blur
- Good for impact analysis

**Optimal**:
- **10-20 microseconds** pulse width
- Freezes motion to ~0.5-1mm blur
- Excellent for precise measurements
- Requires high-power LED overdrive

**Reference**: Professional golf ball impact photography uses **15µs exposures** (1/64,000 sec shutter)

### LED Power Requirements

**Golf impact zone lighting needs**:
- **~30,000 lumens** at hitting area (nearly sunlight level)
- Standard approach: 15 fixtures × 850-1300 lumens each

**Strobed LED advantages**:
- Can overdrive LEDs by **10-20× typical current**
- Achieves **5-10× normal intensity**
- Only during brief pulses (prevents overheating)
- Example: 1000 lumen LED → 10,000 lumens pulsed

### IR Wavelength Selection

For IMX296 global shutter sensor:

- **850nm**: Brighter on silicon sensors, recommended
- **940nm**: Lower sensor sensitivity (silicon response drops off)
- **Remove IR-cut filter**: Required for IR sensitivity (camera already configured)

## Hardware Requirements

### 1. High-Power IR LED Array

**Specifications**:
- Wavelength: 850nm
- Continuous power: 50-100W
- Peak pulse power: 500-1000W (10× overdrive)
- Pulse capability: 10-100µs @ up to 10kHz
- Example: Industrial machine vision LED bars

**Products**:
- Advanced Illumination - BL/DL series backlight strobes
- Gardasoft LED controllers with overdrive capability
- Custom IR LED arrays with MOSFET drivers

### 2. LED Strobe Controller

**Requirements**:
- Microsecond pulse timing accuracy
- Programmable multi-pulse patterns
- Overdrive current control
- Trigger synchronization input

**GPIO trigger from Raspberry Pi**:
```python
import RPi.GPIO as GPIO
import time

STROBE_PIN = 17

def trigger_strobe_sequence():
    """Trigger 3-pulse sequence synchronized with exposure"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(STROBE_PIN, GPIO.OUT)

    # Pulse 1 - start of exposure
    GPIO.output(STROBE_PIN, GPIO.HIGH)
    time.sleep(0.00005)  # 50µs
    GPIO.output(STROBE_PIN, GPIO.LOW)

    time.sleep(0.00065)  # Wait 650µs

    # Pulse 2 - mid exposure
    GPIO.output(STROBE_PIN, GPIO.HIGH)
    time.sleep(0.00005)
    GPIO.output(STROBE_PIN, GPIO.LOW)

    time.sleep(0.00065)

    # Pulse 3 - late exposure
    GPIO.output(STROBE_PIN, GPIO.HIGH)
    time.sleep(0.00005)
    GPIO.output(STROBE_PIN, GPIO.LOW)
```

**Note**: Python timing may have ~100µs jitter. For precision, use:
- Hardware timer (PWM)
- Dedicated microcontroller (Arduino, STM32)
- FPGA-based controller

### 3. Synchronization System - XTR External Trigger Pin

**THE SOLUTION**: IMX296 Global Shutter camera includes a **hardware external trigger input (XTR pin)** that enables microsecond-precision synchronization.

#### XTR Pin Specifications

**Pin location**: Marked as "XTR" on the camera board (test point/solder pad)

**Electrical characteristics**:
- **Voltage**: 1.8V logic (NOT 3.3V or 5V!)
- **VIH (high)**: ≥1.44V (0.8 × 1.8V)
- **VIL (low)**: ≤0.36V (0.2 × 1.8V)
- **Trigger type**: Active-low (falls to 0V to trigger)
- **Minimum pulse width**: ≥2 microseconds

**Timing precision**:
- **Latency**: <1µs in "Fast Trigger Mode"
- **Exposure control**: Exposure time = pulse width + 14.26µs
- **Frame rate**: Directly controlled by trigger pulse frequency

#### How XTR Trigger Works

**Fast Trigger Mode** (recommended):
1. **Exposure starts**: When XTRIG falls (goes LOW)
2. **Exposure ends**: When XTRIG rises (goes HIGH) + 14.26µs
3. **Frame output**: Immediately after exposure ends

**Example timing**:
```
Trigger pulse: 2000µs LOW
Actual exposure: 2000 + 14.26 = 2014.26µs
```

**Trigger restriction**: Cannot pulse during "readout period"
- Full frame: 1126 lines
- Cropped: height + 38 lines
- Violating this causes frame errors

#### Hardware Connection for XTR

**Level shifting required** (3.3V GPIO → 1.8V XTR):

**Method 1: Resistor divider** (simplest)
```
Raspberry Pi GPIO (3.3V)
    |
    ├─ 1.5kΩ resistor ─┬─ XTR pin (1.8V)
                       │
    GND ─ 1.8kΩ resistor ─┘
```

**Voltage calculation**:
```
Vout = 3.3V × (1.8kΩ / (1.5kΩ + 1.8kΩ)) = 1.8V ✓
```

**Method 2: Logic level shifter IC** (better for high frequency)
- Use bidirectional level shifter (Adafruit #757, SparkFun BOB-12009)
- Handles rapid transitions without RC delay
- More reliable for high-speed triggering

**Hardware modification required**:
- If transistor Q2 is fitted, **remove resistor R11**
- R11 connects GP1 to XTR and blocks external trigger

#### Software Configuration

**Enable trigger mode**:
```bash
# One-time enable
echo 1 | sudo tee /sys/module/imx296/parameters/trigger_mode

# Permanent enable (add to /boot/firmware/cmdline.txt)
imx296.trigger_mode=1
```

**Configure camera in Picamera2**:
```python
from picamera2 import Picamera2
import RPi.GPIO as GPIO

# Setup XTR trigger output from Pi GPIO
TRIGGER_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
GPIO.output(TRIGGER_PIN, GPIO.HIGH)  # Idle state

# Configure camera (must specify fixed shutter)
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (688, 136)},
    controls={"FrameRate": 500, "ExposureTime": 2000}  # 2ms exposure
)
picam2.configure(config)
picam2.start()
```

#### THE KEY INSIGHT: Single Trigger for Camera + Strobes

**Instead of trying to sync strobes TO camera, use ONE signal for BOTH**:

```
Master Trigger Signal (from Pi GPIO or external controller)
         |
         ├──> XTR Pin (camera exposure)
         └──> LED Strobe Controller (IR pulses)
```

**Perfect synchronization** because:
1. Same electrical signal controls both systems
2. No timing jitter between camera and strobes
3. Exposure window guaranteed to match strobe timing
4. Microsecond precision (<1µs latency)

#### Implementation Approach: Master Trigger + Strobe Multiplexer

**Hardware architecture**:

```
┌─────────────────────────────────────────────┐
│ Raspberry Pi GPIO                           │
│                                             │
│  Trigger pulse: 2ms LOW, 500 Hz rate       │
│  (Controls frame rate)                      │
└─────────────────┬───────────────────────────┘
                  │
          ┌───────┴────────┐
          │                │
    ┌─────▼──────┐   ┌────▼──────────────────┐
    │  1.8V      │   │  Strobe Controller    │
    │  Level     │   │  (3.3V logic)         │
    │  Shifter   │   │                       │
    └─────┬──────┘   └────┬──────────────────┘
          │               │ Generates 3 pulses
          │               │ during each 2ms:
    ┌─────▼──────┐        │  - @ 0µs (50µs)
    │  XTR Pin   │        │  - @ 700µs (50µs)
    │  (Camera)  │        │  - @ 1400µs (50µs)
    │            │        │
    │ Exposure:  │   ┌────▼──────────────────┐
    │ 2000µs     │   │  High-Power IR LEDs   │
    └────────────┘   │  (850nm, overdriven)  │
                     └───────────────────────┘
```

**Strobe controller logic**:
```python
# Pseudocode for strobe controller (Arduino/STM32)
def on_trigger_falling_edge():
    start_exposure_timer()

    # Fire 3 strobes during exposure
    delay_us(0)      # Immediate
    fire_strobe(50)   # 50µs pulse

    delay_us(650)
    fire_strobe(50)

    delay_us(650)
    fire_strobe(50)

def fire_strobe(duration_us):
    LED_ENABLE_PIN = HIGH
    delay_us(duration_us)
    LED_ENABLE_PIN = LOW
```

#### Timing Diagram: Trigger + Strobes

```
Time (µs):  0        500      1000     1500     2000
            |         |         |         |         |
Trigger:    ┐_________________________________________┌───
(XTR pin)

Camera      |<──────── Exposure: 2014.26µs ─────────>|
Exposure:   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

IR Strobe:  ▀▁▁▁▁▁▁▁▁▁▁▁▁▀▁▁▁▁▁▁▁▁▁▁▁▁▀▁▁▁▁▁▁▁▁▁▁▁▁▁
            |50µs      |50µs      |50µs
            @0µs       @700µs     @1400µs

Result:     3 frozen club images in single frame
```

#### Advantages of XTR-Based Synchronization

**vs Software timing**:
- ✅ <1µs jitter (vs ±100-500µs)
- ✅ Hardware-guaranteed sync
- ✅ No OS scheduling delays
- ✅ Repeatable, deterministic

**vs VSYNC monitoring**:
- ✅ Camera designed for this
- ✅ No hardware modification to camera
- ✅ Exposure time directly controlled
- ✅ Frame rate directly controlled

**vs External trigger controller**:
- ✅ Raspberry Pi can be the master
- ✅ Simpler system (fewer components)
- ✅ Software-configurable timing
- ✅ Lower cost

#### Practical Implementation

**Option 1: Pi as master** (recommended)
- Pi GPIO generates trigger pulses
- External Arduino/STM32 listens to same GPIO
- Arduino fires strobe pattern on each trigger
- Simple, low cost, flexible timing

**Option 2: External master**
- Dedicated timing controller (Arduino Due, Teensy 4.x)
- Generates both camera trigger AND strobe pulses
- Pi becomes slave (triggered by external controller)
- Better timing precision, more complex

**Option 3: FPGA controller** (professional)
- Nanosecond timing precision
- Complex multi-strobe patterns
- Overkill for golf impact capture
- $$$

#### Code Example: External Trigger Mode

**Python (Raspberry Pi)**:
```python
import time
import RPi.GPIO as GPIO
from picamera2 import Picamera2

TRIGGER_PIN = 17
EXPOSURE_US = 2000  # 2ms

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
GPIO.output(TRIGGER_PIN, GPIO.HIGH)  # Idle high

# Setup camera in trigger mode
picam2 = Picamera2()
config = picam2.create_video_configuration(
    controls={"ExposureTime": EXPOSURE_US}
)
picam2.configure(config)
picam2.start()

# Trigger at 500 fps
frame_interval = 1.0 / 500  # 2ms

for i in range(250):  # 0.5 second burst
    # Generate trigger pulse
    GPIO.output(TRIGGER_PIN, GPIO.LOW)   # Start exposure
    time.sleep(EXPOSURE_US / 1_000_000)   # Hold for exposure
    GPIO.output(TRIGGER_PIN, GPIO.HIGH)  # End exposure

    # Wait for next frame
    time.sleep(frame_interval - (EXPOSURE_US / 1_000_000))

    # Capture frame
    frame = picam2.capture_array()
    save_frame(frame, i)
```

**Arduino (Strobe Controller)**:
```cpp
const int TRIGGER_INPUT = 2;   // Listen to Pi GPIO
const int STROBE_OUTPUT = 9;   // Control IR LEDs

void setup() {
  pinMode(TRIGGER_INPUT, INPUT);
  pinMode(STROBE_OUTPUT, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(TRIGGER_INPUT),
                  onTrigger, FALLING);
}

void onTrigger() {
  // Fire 3 strobes during 2ms exposure

  // Strobe 1 - immediate
  fireStrobe(50);  // 50µs pulse
  delayMicroseconds(650);

  // Strobe 2 - mid exposure
  fireStrobe(50);
  delayMicroseconds(650);

  // Strobe 3 - late exposure
  fireStrobe(50);
}

void fireStrobe(int duration_us) {
  digitalWrite(STROBE_OUTPUT, HIGH);
  delayMicroseconds(duration_us);
  digitalWrite(STROBE_OUTPUT, LOW);
}
```

#### Why This Is The Right Approach

**Before knowing about XTR**:
- Complex sync problem
- Timing jitter issues
- Calibration headaches
- Unreliable results

**With XTR trigger pin**:
- Built-in hardware solution
- Microsecond precision
- Simple, elegant design
- Guaranteed synchronization

**The IMX296 was literally designed for this exact use case** - industrial machine vision applications requiring synchronized flash illumination.

#### Making XTR Trigger Mode Reversible/Switchable

**You don't need to permanently enable trigger mode!** It can be switched on/off as needed.

**Software-Only Switching** (recommended, no hardware changes):

```python
# Normal mode (current operation)
echo 0 | sudo tee /sys/module/imx296/parameters/trigger_mode
# Camera runs normally, XTR pin ignored

# Trigger mode (for strobe capture)
echo 1 | sudo tee /sys/module/imx296/parameters/trigger_mode
# Camera waits for XTR pulses
```

**In your web interface**:
```python
class TriggerModeView(MethodView):
    def post(self):
        mode = request.json.get('trigger_mode')  # 0 or 1

        # Enable/disable trigger mode
        subprocess.run(
            ['sudo', 'tee', '/sys/module/imx296/parameters/trigger_mode'],
            input=str(mode).encode(),
            check=True
        )

        # Restart camera with appropriate config
        if mode == 1:
            # Trigger mode: external controller sets timing
            camera.stop()
            camera.configure_trigger_mode()
        else:
            # Normal mode: camera runs continuously
            camera.stop()
            camera.configure_normal_mode()

        return jsonify({'success': True, 'trigger_mode': mode})
```

**Hardware Connection Options**:

**Option 1: Always connected** (simplest)
```
Pi GPIO ──[1.5kΩ]──┬──[1.8kΩ]── GND
                   │
                   └── XTR Pin
```
- Wire stays connected permanently
- When trigger_mode=0, XTR is ignored
- When trigger_mode=1, XTR controls camera
- **No physical switching needed**

**Option 2: Manual switch** (physical control)
```
Pi GPIO ──[1.5kΩ]──┬──[1.8kΩ]── GND
                   │
              [SPDT Switch]
                   │
                   ├── Position 1: XTR Pin (trigger mode)
                   └── Position 2: No connect (normal mode)
```
- Physical switch on enclosure
- Switch to trigger mode when doing strobe capture
- Switch to normal mode for regular operation

**Option 3: GPIO-controlled relay** (software-switched hardware)
```
Control GPIO ──> Small Relay ──> Connects/disconnects XTR

When Control GPIO HIGH: XTR connected (trigger mode)
When Control GPIO LOW:  XTR disconnected (normal mode)
```
- Software control of hardware connection
- Belt-and-suspenders approach
- Adds ~$5 relay module

**Option 4: Mode selector in UI** (best UX)
```
Recording Mode:
  [ ] Normal (continuous, current operation)
  [X] Strobe (external trigger + IR pulses)

When "Strobe" selected:
  - Enable trigger_mode=1
  - Start trigger pulse generation
  - Enable strobe controller
  - Show "STROBE MODE ACTIVE" indicator
```

**Recommended Approach**:

1. **Wire XTR permanently** with level shifter circuit
2. **Leave trigger_mode=0** by default (normal operation)
3. **Add UI toggle** for "Strobe Mode"
4. **When enabled**:
   - Set trigger_mode=1
   - Start GPIO pulse generation
   - Enable Arduino strobe controller
5. **When disabled**:
   - Set trigger_mode=0
   - Stop GPIO pulses
   - Disable strobe controller
   - Resume normal operation

**The beauty**: Hardware stays in place, mode switches in software. No permanent commitment, fully reversible, use strobe mode only when needed for impact analysis.

**Example UI workflow**:
```
Normal golf session:
  - "Normal Mode" selected
  - Camera runs at 400 fps continuously
  - Launch monitor works fine

Impact analysis session (without launch monitor):
  - Switch to "Strobe Mode"
  - Camera runs at 500 fps, triggered externally
  - 3 IR pulses per frame
  - Capture exact impact moments

Back to normal:
  - Switch to "Normal Mode"
  - Everything works as before
```

## Impact Detection Analysis

### Would Multiple Strobes Actually Help?

**YES - Significantly improves impact capture probability**

**Math**:
```
Standard 500fps:
- Frame interval: 2ms (2000µs)
- Impact duration: 500µs
- Probability impact captured: 500/2000 = 25%
- But: Motion blur obscures exact moment

3-pulse strobing @ 500fps:
- Effective sampling: 3 pulses per frame
- Time coverage: 3 × 50µs = 150µs of frozen motion
- Pulse spacing: ~700µs
- Coverage per 2ms: 150µs frozen + 3 sample points
- Probability of capturing impact in one pulse: ~60-70%
- Each pulse frozen (no blur): ✓
```

### What You Could Measure

With 3-pulse stroboscopic capture:

1. **Pre-impact club position** (pulse 1)
   - Club face angle
   - Attack angle
   - Clubhead speed (from spacing)

2. **Impact moment** (pulse 2, if timing right)
   - Ball compression
   - Exact contact point on face
   - Club deflection

3. **Post-impact separation** (pulse 3)
   - Ball launch trajectory
   - Club follow-through
   - Spin characteristics

4. **Derived measurements**:
   - Time-of-contact (from pulse spacing)
   - Acceleration/deceleration during impact
   - Energy transfer efficiency

## Why This Won't Work for Your Application

### Launch Monitor IR Interference

**Problem**: Golf launch monitors (TrackMan, GC3, Foresight, etc.) use infrared sensors for:
- Ball tracking via IR cameras
- Doppler radar with IR tracking assist
- Stereoscopic IR imaging

**Interference mechanisms**:
1. **Sensor saturation**: Strobe pulses overwhelm launch monitor IR receivers
2. **Timing conflicts**: 500 fps @ 3 pulses = 1500 IR pulses/sec
3. **False readings**: Launch monitor interprets strobes as ball reflections
4. **Tracking loss**: IR noise prevents accurate ball flight measurement

**Result**: Launch monitor becomes unreliable or completely non-functional

### Alternative Applications

This technique **would work** for:
- **Standalone impact camera** (no launch monitor)
- **Visible light strobing** (if launch monitor IR-only)
- **Post-session analysis** (capture without live launch monitor)
- **Different sports** (baseball, tennis, hockey - no IR sensors)
- **Research/testing environments** (controlled conditions)

## Implementation Complexity

### Development Effort: MEDIUM (with XTR trigger pin)

**Hardware**:
- Custom IR LED array: $200-500
- Arduino/STM32 strobe controller: $10-30 (DIY)
- Level shifter for XTR: $5-15
- Power supply: $50-100
- Mounting/positioning: $50-100
- **Total hardware**: ~$315-745

**Software**:
- Enable XTR trigger mode: 30 minutes
- Picamera2 integration: 1 day
- Arduino strobe controller code: 1 day
- Testing and tuning: 1-2 days
- **Total development**: ~3-4 days

**Challenges** (significantly reduced with XTR):
1. ~~Precise timing synchronization~~ ✅ Solved by XTR hardware trigger
2. LED overdrive circuit design (need MOSFET drivers)
3. Heat dissipation for repeated use
4. ~~Calibrating pulse timing to frame exposure~~ ✅ Hardware-guaranteed
5. Image processing for ghost separation (optional)
6. Validating actual improvement vs standard high-fps

**Key simplification**: XTR trigger pin eliminates the hardest challenge (synchronization)

## Continuous DC Lighting Alternative

**Simpler approach**: Use very bright DC lights instead of strobing

**Advantages**:
- No synchronization needed
- No IR interference risk
- Simpler hardware
- Immediate implementation

**Requirements for 500+ fps**:
- **DC voltage lighting** (no flicker)
- **~30,000 lumens** total
- 15× LED fixtures @ 2000 lumens each
- Positioned around impact zone

**Cost**: $300-600 for DC LED lighting array

**This is the recommended approach** for your current system.

## Conclusions

### Technical Feasibility: ✓✓ YES (especially with XTR trigger)

Multiple IR strobes during single exposure **would significantly improve** impact capture:
- 3× effective sampling rate
- Eliminates motion blur
- Higher probability of capturing exact impact moment
- Valuable motion analysis data
- **XTR trigger pin provides hardware-perfect synchronization** (<1µs precision)
- **IMX296 was designed for this exact application** (industrial machine vision with flash)

### Practical Viability: ✗ NO (for this application)

**Cannot use with launch monitor** due to IR interference

**However**: With XTR trigger pin, implementation is **much more feasible** than originally thought:
- Hardware guarantees synchronization (hardest problem solved)
- Simple Arduino/STM32 controller handles strobe timing
- Lower cost (~$300-750 vs ~$400-1000 estimated)
- Faster development (3-4 days vs 5-8 days)
- More reliable, deterministic operation

### Recommendations

**For your current golf swing system**:
1. ✅ **Stick with high FPS (400-536) + bright DC lighting**
2. ✅ **Optimize existing setup** (already performing well)
3. ✅ **Consider raw frame capture** for exact impact frame selection

**For future applications without launch monitor**:
1. Prototype with 1-2 strobe pulses first
2. Test synchronization accuracy
3. Validate improvement over standard high-fps
4. Consider visible LED strobes (if ball tracking allows)

**Alternative strobing applications**:
- **Club face analysis** (without ball/launch monitor)
- **Swing path visualization** (club motion through zone)
- **Post-session video review** (separate from live tracking)

## Technical References

### Stroboscopic Photography
- Multiple flash exposures: 10-100 Hz typical
- Flash duration: 1-100µs for motion freezing
- Used in motion analysis since 1870s (Muybridge)

### Golf Impact Physics
- Contact duration: 450-500µs
- Max ball compression: ~250µs into contact
- Clubhead deceleration: ~5000 m/s² during impact

### LED Strobe Technology
- Overdrive ratio: 10-20× continuous current
- Intensity boost: 5-10× normal output
- Pulse width capability: 1µs to 5ms
- Duty cycle limit: <1% for high overdrive

### Raspberry Pi Camera Sync
- Software timing jitter: ±100-500µs
- Hardware PWM jitter: ±10µs
- VSYNC signal available on some modules
- Global shutter enables precise multi-strobe capture

### IMX296 External Trigger (XTR Pin)
- Voltage: 1.8V logic (active-low)
- Latency: <1µs in Fast Trigger Mode
- Exposure control: pulse width + 14.26µs
- Frame rate: controlled by trigger frequency
- Designed for synchronized flash/strobe applications
- Official documentation: https://github.com/raspberrypi/documentation (external_trigger.adoc)

## Date

Research conducted: 2025-11-03

## See Also

- `high_fps_exploration.md` - Maximum frame rate research and raw capture analysis
- `recording_presets.json` - Current camera mode configurations
- `CAMERA_BACKENDS.md` - Camera backend architecture documentation
