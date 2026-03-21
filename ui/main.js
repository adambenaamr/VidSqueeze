const { app, BrowserWindow, Menu } = require('electron')
const nativeImage = require('electron').nativeImage

// TODO: Fix this so that when the user hovers their mouse on the app in the dock,
// it shows the app name properly instead of showing 'Electron'
app.setName('VidSqueeze')

// Instansiable function used to create a general application window
const createWindow = () => {
  const window = new BrowserWindow({
    width: 800,
    height: 600
  })

  window.loadFile('index.html')
}

// Instansiable function used to close all windows of the application
const closeAllWindows = () => {
  const windows = BrowserWindow.getAllWindows()

  for (const window of windows) {
    window.close()
  }
}

// Looks for when the app is ready and creates the window specified from the createWindow() function
app.whenReady().then(() => {
  createWindow()

  // Adds 'right click' menu items that operates and completes various tasks
  const dockMenu = Menu.buildFromTemplate([
    {
      label: 'New Window',
      click: () => { createWindow() }
    },
    {
      label: 'Close All Windows',
      click: () => { closeAllWindows() }
    }
  ])

  app.dock.setMenu(dockMenu)

  // Immitates the macOS behavior where if app is open and there are no active windows, then it opens a new window
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

const image = nativeImage.createFromPath('icon.png')

// Sets the dock app image
app.dock.setIcon(image)

// If the user is not on MacOS and all windows of the application are closed, kill the application entirely
app.on('window-all-closed', () => {
  if (process.platform != 'darwin') app.quit()
})
