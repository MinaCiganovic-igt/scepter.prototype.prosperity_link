from tkinter import filedialog, Tk


def browse(root_directory):
    root = Tk()
    root.withdraw()
    pth = filedialog.askopenfilename(
        initialdir=root_directory,
        title="Scepter - Open - Math Excel File",
        filetypes=(("xls files", ".xls*"),),
    )
    del root
    return pth
