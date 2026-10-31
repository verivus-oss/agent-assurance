use std::io::{Read, Write};
use std::os::fd::AsFd;
use std::os::unix::process::CommandExt;
use std::process::{Child, Command, ExitStatus, Stdio};
use std::time::{Duration, Instant};

use rustix::fs::{OFlags, fcntl_getfl, fcntl_setfl};
use rustix::process::{Pid, Signal, kill_process_group};

struct OwnedChild {
    child: Child,
    group: Pid,
    reaped: bool,
}

impl Drop for OwnedChild {
    fn drop(&mut self) {
        if !self.reaped {
            // Until final wait, the direct child's PID still owns this group
            // identity even if it exited while a descendant retained a pipe.
            let _ = kill_process_group(self.group, Signal::KILL);
            let _ = self.child.kill();
            let _ = self.child.wait();
        }
    }
}

#[derive(Debug)]
pub struct Output {
    pub status: ExitStatus,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

fn nonblocking(fd: &impl AsFd) -> Result<(), String> {
    let flags = fcntl_getfl(fd).map_err(|_| "cannot inspect advisory child pipe")?;
    fcntl_setfl(fd, flags | OFlags::NONBLOCK).map_err(|_| "cannot bound advisory child pipe".into())
}

fn read_available(
    reader: &mut impl Read,
    bytes: &mut Vec<u8>,
    limit: usize,
) -> Result<bool, String> {
    let mut buffer = [0; 65536];
    loop {
        match reader.read(&mut buffer) {
            Ok(0) => return Ok(true),
            Ok(count) => {
                if count > limit - bytes.len() {
                    return Err("advisory child output exceeded its bound".into());
                }
                bytes.extend_from_slice(&buffer[..count]);
                return Ok(false);
            }
            Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => return Ok(false),
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(_) => return Err("cannot read advisory child stream".into()),
        }
    }
}

pub fn run(
    command: &mut Command,
    input: Vec<u8>,
    limit: usize,
    timeout: Duration,
) -> Result<Output, String> {
    if limit == 0 || limit == usize::MAX || timeout.is_zero() {
        return Err("invalid child output or time bound".into());
    }
    let child = command
        .process_group(0)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|_| "cannot start advisory child executable")?;
    let group = Pid::from_raw(
        i32::try_from(child.id()).map_err(|_| "advisory child identity exceeds its bound")?,
    )
    .ok_or("advisory child group identity is absent")?;
    let mut child = OwnedChild {
        child,
        group,
        reaped: false,
    };
    let mut stdin = Some(
        child
            .child
            .stdin
            .take()
            .ok_or("advisory child input is absent")?,
    );
    let mut stdout = child
        .child
        .stdout
        .take()
        .ok_or("advisory child output is absent")?;
    let mut stderr = child
        .child
        .stderr
        .take()
        .ok_or("advisory child diagnostic stream is absent")?;
    nonblocking(stdin.as_ref().ok_or("advisory child input is absent")?)?;
    nonblocking(&stdout)?;
    nonblocking(&stderr)?;
    let (mut output, mut diagnostic) = (Vec::new(), Vec::new());
    let (mut output_done, mut diagnostic_done) = (false, false);
    let mut written = 0;
    let started = Instant::now();
    loop {
        if started.elapsed() >= timeout {
            return Err("advisory child exceeded its deadline".into());
        }
        if let Some(writer) = &mut stdin {
            match writer.write(&input[written..]) {
                Ok(count) => written += count,
                Err(error)
                    if matches!(
                        error.kind(),
                        std::io::ErrorKind::WouldBlock | std::io::ErrorKind::Interrupted
                    ) => {}
                Err(_) => return Err("cannot deliver complete advisory request".into()),
            }
            if written == input.len() {
                stdin = None;
            }
        }
        if !output_done {
            output_done = read_available(&mut stdout, &mut output, limit)?;
        }
        if !diagnostic_done {
            diagnostic_done = read_available(&mut stderr, &mut diagnostic, limit)?;
        }
        // Do not reap before both pipes close: inherited descriptors must be
        // bounded by the same deadline, and group ownership must stay valid.
        if stdin.is_none() && output_done && diagnostic_done {
            if let Some(status) = child
                .child
                .try_wait()
                .map_err(|_| "cannot observe advisory child completion")?
            {
                child.reaped = true;
                return Ok(Output {
                    status,
                    stdout: output,
                    stderr: diagnostic,
                });
            }
        }
        std::thread::sleep(Duration::from_millis(2));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn python(source: &str) -> Command {
        let mut command = Command::new("python3");
        command.args(["-S", "-c", source]);
        command
    }

    #[test]
    fn complete_input_both_output_streams_and_nonzero_status() {
        let input = vec![b'I'; 131072];
        let output = run(&mut python("import sys; data = sys.stdin.buffer.read(); sys.stdout.buffer.write(data); sys.stderr.buffer.write(b'E' * 131072); sys.exit(7)"),
            input.clone(), 131072, Duration::from_secs(10)).expect("complete child");
        assert_eq!(output.status.code(), Some(7));
        assert_eq!(output.stdout, input);
        assert_eq!(output.stderr, vec![b'E'; 131072]);
    }

    #[test]
    fn reject_absent_executable_output_overflow_and_deadline() {
        assert!(
            run(
                &mut Command::new("/nonexistent/dagtoml-osv-transport"),
                vec![],
                64,
                Duration::from_secs(1)
            )
            .unwrap_err()
            .contains("cannot start")
        );
        assert_eq!(
            run(
                &mut python("import sys; sys.stdout.buffer.write(b'X' * 65)"),
                vec![],
                64,
                Duration::from_secs(10)
            )
            .unwrap_err(),
            "advisory child output exceeded its bound"
        );
        assert_eq!(
            run(
                &mut python("import time; time.sleep(10)"),
                vec![],
                64,
                Duration::from_millis(10)
            )
            .unwrap_err(),
            "advisory child exceeded its deadline"
        );
        assert!(run(&mut python("pass"), vec![], 0, Duration::from_secs(1)).is_err());
        assert!(run(&mut python("pass"), vec![], 64, Duration::ZERO).is_err());
    }

    #[test]
    fn descendant_held_pipes_remain_inside_the_deadline() {
        for source in [
            "import os,time; pid=os.fork(); os._exit(0) if pid else time.sleep(10)",
            "import os,time; pid=os.fork(); os._exit(0) if pid else (os.setsid(),time.sleep(0.3))",
        ] {
            let started = Instant::now();
            assert_eq!(
                run(&mut python(source), vec![], 64, Duration::from_millis(100)).unwrap_err(),
                "advisory child exceeded its deadline"
            );
            assert!(started.elapsed() < Duration::from_secs(2));
        }
    }
}
