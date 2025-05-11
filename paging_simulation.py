import tkinter as tk
from tkinter import ttk
import time

# 内存和页面参数
MEMORY_SIZE = 64 * 1024  # 64KB
BLOCK_SIZE = 1024  # 1024字节
NUM_BLOCKS = MEMORY_SIZE // BLOCK_SIZE  # 64个内存块
PAGE_SIZE = BLOCK_SIZE  # 页大小等于块大小
MAX_JOB_SIZE = 64 * 1024  # 作业最大64KB
NUM_PAGES = MAX_JOB_SIZE // PAGE_SIZE  # 64页

# 页表项
# 页号、标志位、内存块号、修改标志、磁盘位置
class PageTableEntry:
    def __init__(self, page_number, disk_location):
        self.page_number = page_number
        self.present = False
        self.frame_number = None
        self.modified = False
        self.disk_location = disk_location

# 页式管理模拟类
# 页表、内存块、FIFO队列、已使用的内存块索引
class PagingSimulation:
    def __init__(self, num_frames, memory_blocks):
        self.num_frames = num_frames
        self.page_table = [PageTableEntry(i, f'{i:03d}') for i in range(NUM_PAGES)]
        self.memory_frames = memory_blocks.copy()  # 存储用户输入的内存块号
        self.fifo_queue = []  # 先进先出队列
        self.used_frames = []  # 记录已使用的内存块索引
    
    def access_page(self, page_number, offset, is_write=False):
        # 从页表中获取指定页号对应的页表项
        entry = self.page_table[page_number]
        # 判断是否发生缺页中断，若页面不在物理内存中（present 为 False），则发生缺页
        page_fault = not entry.present
        # 初始化被淘汰的页面号为 None
        victim_page_number = None

        if page_fault:
            if len(self.used_frames) < self.num_frames:
                # 若已使用的内存块数量小于总内存帧数，说明有空闲内存块
                # 新分配的内存块索引为已使用内存块列表的长度
                frame_index = len(self.used_frames)
                # 根据索引从内存块列表中获取对应的内存块号
                frame_number = self.memory_frames[frame_index]
                # 将新分配的内存块索引添加到已使用内存块列表中
                self.used_frames.append(frame_index)
            else:
                # 若内存已满，需要进行页面置换
                # 使用 FIFO 算法，从队列头部取出最早进入的页面号作为被淘汰的页面号
                victim_page_number = self.fifo_queue.pop(0)
                # 获取被淘汰页面的页表项
                victim_entry = self.page_table[victim_page_number]
                # 将被淘汰页面的存在位设为 False，表示该页面已不在物理内存中
                victim_entry.present = False
                if victim_entry.modified:
                    # 若被淘汰页面被修改过，需要将其写回磁盘
                    # 此处代码占位，实际应用中需实现写回磁盘的逻辑
                    pass
                # 从已使用内存块列表中取出最早使用的内存块索引
                frame_index = self.used_frames.pop(0)
                # 根据索引从内存块列表中获取对应的内存块号
                frame_number = self.memory_frames[frame_index]
                # 将该内存块索引重新添加到已使用内存块列表尾部
                self.used_frames.append(frame_index)

            # 将当前请求的页面标记为已存在于物理内存中
            entry.present = True
            # 为当前请求的页面分配物理内存块号
            entry.frame_number = frame_number
            # 根据操作类型更新修改位
            entry.modified = is_write
            # 将当前请求的页面号添加到 FIFO 队列尾部
            self.fifo_queue.append(page_number)
            # 确保已使用内存块列表的长度不超过总内存帧数
            if len(self.used_frames) > self.num_frames:
                self.used_frames = self.used_frames[-self.num_frames:]

        else:
            if is_write:
                # 若未发生缺页且是写操作，将页面的修改位设为 True
                entry.modified = True

        # 计算物理地址，将帧号左移 10 位（因为页大小为 1024 字节，2^10 = 1024），再加上页内偏移
        physical_address = (entry.frame_number << 10) + offset
        # 返回物理地址、是否缺页、页表项和被淘汰的页面号
        return physical_address, page_fault, entry, victim_page_number

class SimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("请求式分页管理模拟")
        self.root.minsize(width=600, height=400)  # 设置窗口最小宽度
        self.instructions = []
        self.current_index = 0
        
        # 新增：内存块输入界面
        self.create_memory_block_input()
        
        # 创建输入界面
        self.create_input_widgets()
        
        # 创建界面组件
        self.create_widgets()

    def create_memory_block_input(self):
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=5, fill=tk.X, padx=10)  # 缩小上下间距，添加左右边距

        ttk.Label(input_frame, text="内存块(4个，用空格分隔):").pack(side=tk.LEFT, padx=3)
        self.memory_block_entry = ttk.Entry(input_frame, width=20)
        self.memory_block_entry.pack(side=tk.LEFT, padx=3)

        # 初始化模拟按钮
        self.init_button = ttk.Button(input_frame, text="初始化模拟", command=self.init_simulation, state=tk.NORMAL)
        self.init_button.pack(side=tk.LEFT, padx=5)

    def init_simulation(self):
        try:
            memory_blocks = list(map(int, self.memory_block_entry.get().split()))
            if len(memory_blocks) != 4:
                tk.messagebox.showerror("输入错误", "请输入4个用空格分隔的内存块编号。")
                return
            
            self.num_frames = 4
            self.simulator = PagingSimulation(self.num_frames, memory_blocks)  # 传递内存块编号
            self.init_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL if self.instructions else tk.DISABLED)
            self.update_page_table_display()
        except ValueError:
            tk.messagebox.showerror("输入错误", "请输入有效的整数。")

    def create_input_widgets(self):
        # 输入标签和输入框
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=5, fill=tk.X, padx=10)  # 缩小上下间距，添加左右边距

        ttk.Label(input_frame, text="序号:").pack(side=tk.LEFT, padx=3)
        self.index_entry = ttk.Entry(input_frame, width=8)  # 缩小输入框宽度
        self.index_entry.pack(side=tk.LEFT, padx=3)

        ttk.Label(input_frame, text="操作:").pack(side=tk.LEFT, padx=3)
        self.operation_entry = ttk.Entry(input_frame, width=10)  # 缩小输入框宽度
        self.operation_entry.pack(side=tk.LEFT, padx=3)

        ttk.Label(input_frame, text="页号:").pack(side=tk.LEFT, padx=3)
        self.page_number_entry = ttk.Entry(input_frame, width=8)  # 缩小输入框宽度
        self.page_number_entry.pack(side=tk.LEFT, padx=3)

        ttk.Label(input_frame, text="页内地址:").pack(side=tk.LEFT, padx=3)
        self.offset_entry = ttk.Entry(input_frame, width=8)  # 缩小输入框宽度
        self.offset_entry.pack(side=tk.LEFT, padx=3)

        # 添加指令按钮
        ttk.Button(input_frame, text="添加指令", command=self.add_instruction).pack(side=tk.LEFT, padx=5)

        # 开始模拟按钮
        self.start_button = ttk.Button(input_frame, text="开始模拟", command=self.start_simulation, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=5)

    def create_widgets(self):
        # 指令列表
        self.instruction_tree = ttk.Treeview(self.root, columns=("序号", "操作", "页号", "页内地址", "物理地址", "缺页情况"), show="headings")
        self.instruction_tree.heading("序号", text="序号")
        self.instruction_tree.heading("操作", text="操作")
        self.instruction_tree.heading("页号", text="页号")
        self.instruction_tree.heading("页内地址", text="页内地址")
        self.instruction_tree.heading("物理地址", text="物理地址")
        self.instruction_tree.heading("缺页情况", text="缺页情况")
        self.instruction_tree.pack(pady=5, fill=tk.BOTH, expand=True, padx=10)  # 缩小上下间距，添加左右边距
        
        # 页表显示
        self.page_table_tree = ttk.Treeview(self.root, columns=("页号", "标志", "内存块号", "修改标志", "磁盘位置"), show="headings")
        self.page_table_tree.heading("页号", text="页号")
        self.page_table_tree.heading("标志", text="标志")
        self.page_table_tree.heading("内存块号", text="内存块号")
        self.page_table_tree.heading("修改标志", text="修改标志")
        self.page_table_tree.heading("磁盘位置", text="磁盘位置")
        self.page_table_tree.pack(pady=5, fill=tk.BOTH, expand=True, padx=10)  # 缩小上下间距，添加左右边距

    def add_instruction(self):
        try:
            index = int(self.index_entry.get())
            operation = self.operation_entry.get()
            page_number = int(self.page_number_entry.get())
            offset = int(self.offset_entry.get())
            
            self.instructions.append((index, operation, page_number, offset))
            
            # 清空输入框
            self.index_entry.delete(0, tk.END)
            self.operation_entry.delete(0, tk.END)
            self.page_number_entry.delete(0, tk.END)
            self.offset_entry.delete(0, tk.END)
            
            # 启用开始模拟按钮
            if not self.instructions:
                self.start_button.config(state=tk.DISABLED)
            else:
                self.start_button.config(state=tk.NORMAL)
        except ValueError:
            pass

    def create_widgets(self):
        # 指令列表
        self.instruction_tree = ttk.Treeview(self.root, columns=("序号", "操作", "页号", "页内地址", "物理地址", "缺页情况"), show="headings")
        self.instruction_tree.heading("序号", text="序号")
        self.instruction_tree.heading("操作", text="操作")
        self.instruction_tree.heading("页号", text="页号")
        self.instruction_tree.heading("页内地址", text="页内地址")
        self.instruction_tree.heading("物理地址", text="物理地址")
        self.instruction_tree.heading("缺页情况", text="缺页情况")
        self.instruction_tree.pack(pady=10)
        
        # 页表显示
        self.page_table_tree = ttk.Treeview(self.root, columns=("页号", "标志", "内存块号", "修改标志", "磁盘位置"), show="headings")
        self.page_table_tree.heading("页号", text="页号")
        self.page_table_tree.heading("标志", text="标志")
        self.page_table_tree.heading("内存块号", text="内存块号")
        self.page_table_tree.heading("修改标志", text="修改标志")
        self.page_table_tree.heading("磁盘位置", text="磁盘位置")
        self.page_table_tree.pack(pady=10)

    def start_simulation(self):
        self.start_button.config(state=tk.DISABLED)
        self.simulate_next_instruction()
        
    def simulate_next_instruction(self):
        if self.current_index < len(self.instructions):
            index, operation, page_number, offset = self.instructions[self.current_index]
            is_write = operation in ['存(save)']
            
            # 支持所有操作
            if operation in ['+', '-', '/', '*', '取(load)']:
                is_write = False
            elif operation == '存(save)':
                is_write = True
            
            physical_address, page_fault, entry, victim_page = self.simulator.access_page(page_number, offset, is_write)
            
            if page_fault:
                if victim_page is None:
                    page_fault_info = "缺页，分配新内存块"
                else:
                    page_fault_info = f"缺页，淘汰第{victim_page}页"
            else:
                page_fault_info = "不缺页"
            
            # 更新指令列表
            self.instruction_tree.insert('', 'end', values=(index, operation, page_number, offset, physical_address, page_fault_info))
            
            # 更新页表显示
            self.update_page_table_display()
            
            self.current_index += 1
            self.root.after(1000, self.simulate_next_instruction)  # 每秒执行一条指令
        else:
            self.start_button.config(state=tk.NORMAL)
            
    def update_page_table_display(self):
        # 清空页表显示
        for i in self.page_table_tree.get_children():
            self.page_table_tree.delete(i)
        
        # 重新填充页表显示
        for entry in self.simulator.page_table:
            self.page_table_tree.insert('', 'end', values=(entry.page_number, int(entry.present), entry.frame_number if entry.present else "", int(entry.modified), entry.disk_location))

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()