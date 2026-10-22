# Actualizador de propiedades (self-hosted runner)

RE/MAX bloquea con `403 Forbidden` las IPs de datacenter de GitHub Actions, así que
el workflow [`scrape.yml`](.github/workflows/scrape.yml) corre en una computadora
propia (Mac o Windows) con conexión hogareña. GitHub le manda el trabajo a esa
computadora, que scrapea y publica `docs/data/propiedades.json`.

- Corre todos los días a las **9 AM (hora de Buenos Aires)**.
- Si a esa hora la computadora está apagada o dormida, el trabajo **queda en espera
  hasta 24 h** y se ejecuta apenas la máquina vuelve a estar en línea.
- No hace falta tener una terminal abierta: el runner queda instalado como servicio.

> **Permisos:** registrar un runner requiere ser **admin** del repositorio
> (`javofrank`). Los pasos de "Obtener el token" los tiene que hacer Javier desde su
> cuenta, o darle rol admin a quien lo instale.

## 1. Obtener el token (en GitHub, cualquier plataforma)

1. Abrir <https://github.com/javofrank/javierfrank.ar/settings/actions/runners/new>.
2. Elegir el sistema operativo (**macOS** + **ARM64** para una Mac con chip M1/M2/M3/M4,
   **x64** para una Mac Intel; o **Windows**).
3. La página muestra los comandos de *Download* y *Configure* con un token que vence
   en una hora. Usarlos en los pasos de abajo.

## 2a. Instalación en la Mac de Javier

Requisitos previos (una sola vez):

- **Google Chrome** instalado.
- **Python 3** desde <https://www.python.org/downloads/macos/> (el instalador oficial).
  Evitar el `python3` que trae macOS, porque pide instalar las Xcode Command Line Tools.

En la app **Terminal**:

```bash
mkdir ~/actions-runner && cd ~/actions-runner
# Pegar acá los comandos "Download" que muestra GitHub (curl + tar).
./config.sh --url https://github.com/javofrank/javierfrank.ar --token <TOKEN> --unattended --name mac-javier
./svc.sh install
./svc.sh start
```

`svc.sh install` lo registra como servicio de `launchd`, así que **arranca solo cada vez
que Javier inicia sesión**. No tiene que hacer nada más.

Para verificarlo: en <https://github.com/javofrank/javierfrank.ar/settings/actions/runners>
el runner tiene que figurar como **Idle** (verde).

### Que la Mac se despierte sola (opcional, recomendado)

Una Mac dormida no ejecuta nada. Para que se despierte unos minutos antes de las 9 AM:

```bash
sudo pmset repeat wakeorpoweron MTWRFSU 08:55:00
```

(Se deshace con `sudo pmset repeat cancel`.) También sirve el ajuste de
*Configuración del Sistema → Batería/Energía → Opciones →
"Activar para acceso a la red"*.

### Íconos de doble clic para Javier

En la carpeta [`mac/`](mac/) hay dos archivos para copiar al Escritorio o al Dock:

| Archivo | Qué hace |
|---|---|
| `Iniciar actualizador.command` | Arranca el servicio si se hubiera detenido y avisa si está funcionando. |
| `Actualizar propiedades ahora.command` | Abre la página del workflow en GitHub; ahí se toca **Run workflow → Run workflow** para actualizar al momento. |

La primera vez macOS puede decir que el archivo "no se puede abrir porque es de un
desarrollador no identificado". En ese caso: clic derecho → **Abrir** → **Abrir**. Solo
se pregunta una vez.

**Alternativa con Automator** (para tener una app con ícono propio):

1. Abrir **Automator** → *Nuevo documento* → **Aplicación**.
2. Agregar la acción **Ejecutar script de shell** y pegar:
   ```bash
   cd ~/actions-runner && ./svc.sh start
   open "https://github.com/javofrank/javierfrank.ar/actions/workflows/scrape.yml"
   ```
3. Guardar como `Actualizar propiedades.app` en *Aplicaciones* y arrastrarla al Dock.
   (Para cambiarle el ícono: *Obtener información* y pegar una imagen sobre el ícono.)

### ¿Y con cron?

No hace falta: el horario ya lo maneja GitHub (`schedule` en `scrape.yml`) y el
servicio de `launchd` mantiene el runner vivo. Si alguna vez se quisiera prescindir del
runner, `scrape-local.sh` se puede cronear (instrucciones en el propio script). Pero esa
opción necesita credenciales de git guardadas en la Mac. El runner no las necesita.

## 2b. Instalación en Windows

Requisitos: **Google Chrome** y **Python 3** (con *Add python.exe to PATH* marcado).

En PowerShell **como administrador**:

```powershell
mkdir C:\actions-runner; cd C:\actions-runner
# Pegar acá los comandos "Download" que muestra GitHub (Invoke-WebRequest + Expand-Archive).
.\config.cmd --url https://github.com/javofrank/javierfrank.ar --token <TOKEN> --unattended --name pc-jorge --runasservice
```

Con `--runasservice` queda como servicio de Windows y arranca con la PC. Python y Chrome
tienen que estar instalados para todos los usuarios o en el `PATH` del sistema, porque el
servicio corre con otra cuenta (`NETWORK SERVICE`). Si da problemas, se puede
configurar sin `--runasservice` y lanzarlo con `run.cmd` (queda una ventana abierta).

## Usar dos runners a la vez

Si están registradas las dos computadoras (Mac y Windows), GitHub le da el trabajo a la
primera que esté libre. El `concurrency` del workflow evita que corran dos a la vez.

## Seguridad

El repositorio es **público**. Este workflow solo se dispara por horario o a mano, así
que nadie de afuera puede ejecutar código en la computadora del runner. **No agregar
workflows que se disparen con `pull_request`** mientras haya un self-hosted runner
registrado, porque un fork podría correr código en esa máquina.

## Desinstalar

Mac: `cd ~/actions-runner && ./svc.sh stop && ./svc.sh uninstall && ./config.sh remove --token <TOKEN>`
(el token de remoción se obtiene en la misma página de runners → el runner → *Remove*).
