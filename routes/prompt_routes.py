"""
Prompt 配置管理路由藍圖
用途：處理 SYSTEM PROMPT 配置的 CRUD 操作
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from services import load_prompts_config, save_prompts_config

# 創建 Prompt 管理藍圖
prompt_bp = Blueprint('prompt', __name__)


@prompt_bp.route('/api/prompts/list', methods=['GET'])
def get_prompts_list():
    """
    獲取配置列表路由

    用途：返回所有可用的 Prompt 配置名稱和默認配置

    返回：
        success (bool): 是否成功
        configs (list): 配置名稱列表
        default_config (str): 默認配置名稱
    """
    try:
        config = load_prompts_config()
        return jsonify({
            'success': True,
            'configs': list(config['prompts'].keys()),
            'default_config': config['default_config']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@prompt_bp.route('/api/prompts/get', methods=['GET'])
def get_prompt_config():
    """
    獲取配置詳情路由

    用途：返回特定配置的完整內容

    查詢參數：
        config_name (str): 配置名稱

    返回：
        success (bool): 是否成功
        config (dict): 配置內容（包含所有功能的 prompt）
    """
    try:
        config_name = request.args.get('config_name')
        if not config_name:
            return jsonify({
                'success': False,
                'error': '缺少 config_name 參數'
            })

        config = load_prompts_config()
        if config_name not in config['prompts']:
            return jsonify({
                'success': False,
                'error': f'找不到配置: {config_name}'
            })

        return jsonify({
            'success': True,
            'config': config['prompts'][config_name]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@prompt_bp.route('/api/prompts/save', methods=['POST'])
def save_prompt_config():
    """
    保存/更新配置路由

    用途：保存或更新特定配置的內容（僅可編輯部分）

    流程：
    1. 接收配置名稱和 prompt 內容
    2. 驗證可編輯部分不包含規則和範例標記
    3. 如果配置已存在，更新可編輯部分並保留 fixed 部分
    4. 如果配置不存在，創建新配置
    5. 更新時間戳
    6. 保存到配置文件

    請求參數：
        config_name (str): 配置名稱
        prompts (dict): Prompt 內容（包含各功能的 editable 和 fixed 部分）

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
    """
    try:
        data = request.json
        config_name = data.get('config_name')
        prompts = data.get('prompts')

        if not config_name or not prompts:
            return jsonify({
                'success': False,
                'error': '缺少必要參數'
            })

        # 驗證可編輯部分不包含規則和範例標記
        for func_name, func_prompt in prompts.items():
            if 'editable' in func_prompt:
                if '【規則】' in func_prompt['editable'] or '【範例】' in func_prompt['editable']:
                    return jsonify({
                        'success': False,
                        'error': f'{func_name}: 可編輯區域不能包含【規則】或【範例】標記'
                    })

        config = load_prompts_config()

        # 更新配置
        if config_name in config['prompts']:
            # 更新現有配置，保留 fixed 部分
            existing_config = config['prompts'][config_name]
            for func_name, func_prompt in prompts.items():
                if func_name in existing_config:
                    existing_config[func_name]['editable'] = func_prompt.get('editable', existing_config[func_name]['editable'])
            existing_config['updated_at'] = datetime.now().isoformat()
        else:
            # 新增配置
            config['prompts'][config_name] = {
                'name': config_name,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                **prompts
            }

        save_prompts_config(config)

        return jsonify({
            'success': True,
            'message': '配置已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@prompt_bp.route('/api/prompts/create', methods=['POST'])
def create_prompt_config():
    """
    創建新配置路由

    用途：創建新的 Prompt 配置（複製預設配置）

    流程：
    1. 接收新配置名稱
    2. 檢查名稱是否已存在
    3. 複製預設配置的所有功能 prompt
    4. 設置創建和更新時間戳
    5. 保存到配置文件

    請求參數：
        config_name (str): 新配置名稱

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
    """
    try:
        data = request.json
        config_name = data.get('config_name')

        if not config_name:
            return jsonify({
                'success': False,
                'error': '缺少配置名稱'
            })

        config = load_prompts_config()

        if config_name in config['prompts']:
            return jsonify({
                'success': False,
                'error': '配置名稱已存在'
            })

        # 複製預設配置
        default_config_name = config['default_config']
        default_config = config['prompts'][default_config_name]

        new_config = {
            'name': config_name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 複製所有功能的 prompt
        for func_name in ['import_scenario', 'star_scenario', 'get_wta', 'text_generation', 'military_rag']:
            if func_name in default_config:
                new_config[func_name] = {
                    'editable': default_config[func_name]['editable'],
                    'fixed': default_config[func_name]['fixed']
                }

        config['prompts'][config_name] = new_config
        save_prompts_config(config)

        return jsonify({
            'success': True,
            'message': f'配置 {config_name} 已創建'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@prompt_bp.route('/api/prompts/delete', methods=['DELETE'])
def delete_prompt_config():
    """
    刪除配置路由

    用途：刪除指定的 Prompt 配置（不能刪除預設配置）

    查詢參數：
        config_name (str): 要刪除的配置名稱

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
    """
    try:
        config_name = request.args.get('config_name')

        if not config_name:
            return jsonify({
                'success': False,
                'error': '缺少配置名稱'
            })

        config = load_prompts_config()

        # 不能刪除預設配置
        if config_name == '預設配置':
            return jsonify({
                'success': False,
                'error': '不能刪除預設配置'
            })

        if config_name not in config['prompts']:
            return jsonify({
                'success': False,
                'error': '配置不存在'
            })

        del config['prompts'][config_name]
        save_prompts_config(config)

        return jsonify({
            'success': True,
            'message': f'配置 {config_name} 已刪除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@prompt_bp.route('/api/prompts/rename', methods=['POST'])
def rename_prompt_config():
    """
    重命名配置路由

    用途：重命名指定的 Prompt 配置（不能重命名預設配置）

    流程：
    1. 接收舊名稱和新名稱
    2. 驗證舊配置存在且不是預設配置
    3. 驗證新名稱不存在
    4. 複製配置並更新名稱和時間戳
    5. 刪除舊配置
    6. 如果舊配置是默認配置，更新默認配置指向
    7. 保存到配置文件

    請求參數：
        old_name (str): 舊配置名稱
        new_name (str): 新配置名稱

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
    """
    try:
        data = request.json
        old_name = data.get('old_name')
        new_name = data.get('new_name')

        if not old_name or not new_name:
            return jsonify({
                'success': False,
                'error': '缺少參數'
            })

        config = load_prompts_config()

        # 不能重命名預設配置
        if old_name == '預設配置':
            return jsonify({
                'success': False,
                'error': '不能重命名預設配置'
            })

        if old_name not in config['prompts']:
            return jsonify({
                'success': False,
                'error': '原配置不存在'
            })

        if new_name in config['prompts']:
            return jsonify({
                'success': False,
                'error': '新配置名稱已存在'
            })

        # 重命名
        config['prompts'][new_name] = config['prompts'][old_name]
        config['prompts'][new_name]['name'] = new_name
        config['prompts'][new_name]['updated_at'] = datetime.now().isoformat()
        del config['prompts'][old_name]

        # 如果是預設配置，更新預設配置名稱
        if config['default_config'] == old_name:
            config['default_config'] = new_name

        save_prompts_config(config)

        return jsonify({
            'success': True,
            'message': f'配置已重命名為 {new_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
